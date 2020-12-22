from contextlib import contextmanager
import json
import logging
from io import TextIOWrapper
from typing import Dict, Callable, Iterable, List, Tuple, Union

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import numpy as np
from numpy import asarray, concatenate, ones
from osgeo import gdal
from osgeo import osr
from shapely.geometry.base import BaseGeometry
from shapely.geometry import shape

from tilesgis.types import ExtentDegrees, AreaData

logger = logging.getLogger(__name__)

# NOTE these three classes are from https://github.com/benjimin/descartes/blob/master/descartes/patch.py
# it's basically the only code I could find that does this -_-


class Polygon:
    # Adapt Shapely or GeoJSON/geo_interface polygons to a common interface
    def __init__(self, context):
        if hasattr(context, 'interiors'):
            self.context = context
        else:
            self.context = getattr(context, '__geo_interface__', context)

    @property
    def geom_type(self):
        return (getattr(self.context, 'geom_type', None)
                or self.context['type'])

    @property
    def exterior(self):
        return (getattr(self.context, 'exterior', None)
                or self.context['coordinates'][0])

    @property
    def interiors(self):
        value = getattr(self.context, 'interiors', None)
        if value is None:
            value = self.context['coordinates'][1:]
        return value


def to_polygon_path(polygon):
    """Constructs a compound matplotlib path from a Shapely or GeoJSON-like
    geometric object"""
    this = Polygon(polygon)
    assert this.geom_type == 'Polygon'

    def coding(ob):
        # The codes will be all "LINETO" commands, except for "MOVETO"s at the
        # beginning of each subpath
        n = len(getattr(ob, 'coords', None) or ob)
        vals = ones(n, dtype=Path.code_type) * Path.LINETO
        vals[0] = Path.MOVETO
        return vals
    vertices = concatenate(
                    [asarray(this.exterior)[:, :2]]
                    + [asarray(r)[:, :2] for r in this.interiors])
    codes = concatenate(
                [coding(this.exterior)]
                + [coding(r) for r in this.interiors])
    return Path(vertices, codes)


def create_polygon_patch(polygon, **kwargs):
    """Constructs a matplotlib patch from a geometric object

    The `polygon` may be a Shapely or GeoJSON-like object with or without holes.
    The `kwargs` are those supported by the matplotlib.patches.Polygon class
    constructor. Returns an instance of matplotlib.patches.PathPatch.
    Example (using Shapely Point and a matplotlib axes):
      >>> b = Point(0, 0).buffer(1.0)
      >>> patch = PolygonPatch(b, fc='blue', ec='blue', alpha=0.5)
      >>> axis.add_patch(patch)
    """
    return PathPatch(to_polygon_path(polygon), **kwargs)


def coord_to_pixel(lat: float, lon: float, height: float, width: float, extent: ExtentDegrees) -> Tuple[float, float]:
    """Convert lat/lon coordinate to a pixel coordinate for a given area.

    NOTE: this assumes the extent is very small, enough to not introduce errors
    due to curvature. For this project is usually no bigger than a city.
    """
    x = (lon - extent.lonmin) * width / (extent.lonmax - extent.lonmin)
    y = (lat - extent.latmin) * height / (extent.latmax - extent.latmin)

    return x, y


def _representation_iterator(
    data: AreaData,
    entity_callback,
        ):
    for w in data.ways.values():
        if w.geoJSON is None:
            continue
        representation = entity_callback(w)
        if representation is not None:
            yield (w.geoJSON, representation)

    for r in data.relations.values():
        if r.geoJSON is None:
            continue
        representation = entity_callback(r)
        if representation is not None:
            yield (r.geoJSON, representation)
    for p in data.nodes.values():
        if p.geoJSON is None:
            continue
        representation = entity_callback(p)
        if representation is not None:
            yield (p.geoJSON, representation)


@contextmanager
def _read_file(target_file: Union[str, TextIOWrapper]):
    if isinstance(target_file, str):
        try:
            fh = open(target_file, 'r')
            yield fh
        finally:
            fh.close()
    elif isinstance(target_file, TextIOWrapper):
        yield target_file
    else:
        raise TypeError(f'Invalid type {type(target_file)}')


@contextmanager
def _write_file(target_file: Union[str, TextIOWrapper]):
    if isinstance(target_file, str):
        try:
            fh = open(target_file, 'w')
            yield fh
        finally:
            fh.close()
    elif isinstance(target_file, TextIOWrapper):
        yield target_file
    else:
        raise TypeError(f'Invalid type {type(target_file)}')


def data_to_representation(
    data: AreaData,
    entity_callback: Callable,
        ) -> List[Tuple[str, dict]]:

    representations = []
    for geoJSON, repr in _representation_iterator(data, entity_callback):
        representations.append((geoJSON, repr))
    return representations


def data_to_representation_file(
    data: AreaData,
    target_file: Union[str, TextIOWrapper],
    entity_callback: Callable,
):
    with _write_file(target_file) as fh:
        for geoJSON, repr in _representation_iterator(data, entity_callback):
            fh.write(json.dumps(dict(
                geojson=geoJSON,
                representation=repr,
            )))
            fh.write('\n')


def file_to_representation(target_file: Union[str, TextIOWrapper]):
    with _read_file(target_file) as fh:
        for line in fh:
            obj = json.loads(line)
            yield (obj['geojson'], obj['representation'])


def representation_to_figure(
    representations: Iterable[Tuple[str, dict]],
    extent: ExtentDegrees,
    representer: Callable,
    figsize: int = 1500,
        ) -> Figure:

    to_draw = []

    for representation in representations:
        shapely_obj = shape(json.loads(representation[0]))
        res = representer(representation[1], shape=shapely_obj)
        # TODO not very beautiful, what's the best way to allow an optional return value?
        # maybe having two callbacks, one that receives and return the shape
        # and the other for pure rendering?
        # also, in this second case it should return a list of shapes and representations
        # Nah, probably better to have independent pipelines for (shapes, repr) tuples
        # allowing filtering, aggregations and whatnot
        if isinstance(res, tuple):
            draw_options, new_shape = res
        else:
            draw_options, new_shape = res, None
        to_draw.append((
            shapely_obj if new_shape is None else new_shape,
            draw_options,
            ))
    return render_shapes_to_figure(extent, to_draw, figsize)


def render_shapes_to_figure(
    extent: ExtentDegrees,
    to_draw: List[Tuple[BaseGeometry, Dict]],
    figsize: int = 1500
        ) -> Figure:
    """Renders arbitrary Shapely geometrical objects to a Figure.

    This is quite ambitious!

    the to_draw argument is a list of Shapely geometrical objects and rules to
    draw them (color, style, etc.)
    """
    fig = Figure(figsize=(5, 5), dpi=figsize / 5, frameon=False)
    ax = fig.add_subplot()
    ax.set_ylim(extent.latmin, extent.latmax)
    ax.set_xlim(extent.lonmin, extent.lonmax)
    # the following lines are the result of an ABSURD amount of attempts
    # I really hope one day matplotlib will become more intuitive ;_;
    ax.set_xmargin(0.0)
    ax.set_ymargin(0.0)
    ax.set_axis_off()

    fig.subplots_adjust(bottom=0)
    fig.subplots_adjust(top=1)
    fig.subplots_adjust(right=1)
    fig.subplots_adjust(left=0)

    for geom, options in to_draw:
        # the possible types are FeatureCollection, Feature, Point, LineString, MultiPoint,
        # Polygon, MultiLineString, MultiPolygon, and GeometryCollection
        # however I found only these three so far
        try:
            if geom.type == 'LineString':
                x, y = geom.xy
                ax.plot(x, y, **options)
                continue

            if geom.type == 'Polygon':
                patch = create_polygon_patch(geom, **options)
                ax.add_patch(patch)
                continue

            if geom.type == 'Point':
                x, y = geom.xy
                ax.scatter(x, y, **options)
                continue

            raise ValueError(f'Cannot draw type {geom.type}')

        except AttributeError:
            logger.exception(f'Error drawing, will skip {geom}, options: {options}')

    return fig


def figure_to_numpy(fig: Figure) -> np.ndarray:
    """Render a matplotlib Figure to a Numpy array."""
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    buf = canvas.buffer_rgba()
    # convert to a NumPy array, flip to deal with the y axis
    return np.flipud(np.asarray(buf))


def save_to_geoTIFF(bbox: ExtentDegrees, image: np.ndarray, fname: str):
    """Save a Numpy image as a geoTIFF for the given extent.

    The image is expected to be flipped on the Y axis, as is the case
    when using the functions in this module.

    Currently the image must be a square otherwise is stretched,
    notice that using the extent metadata it will look fine even when the
    extent is not square at all.

    Alpha channel is ignored if it exists.

    Parameters
    ----------
    bbox : ExtentDegrees
        The extent for this image
    image : numpy.ndarray
        The image, as a ndarray of shape N, N, 3
    fname : str
        The ouput path, relative or absolute
    """
    nx, ny = image.shape[:2]
    # this is because the image is distorted if not square
    assert nx == ny, 'Image is not a square'
    xres = (bbox.lonmax - bbox.lonmin) / nx
    yres = (bbox.latmax - bbox.latmin) / ny
    geotransform = (bbox.lonmin, xres, 0, bbox.latmax, 0, -yres)

    dst_ds = gdal.GetDriverByName('GTiff').Create(fname, ny, nx, 3, gdal.GDT_Byte)

    srs = osr.SpatialReference()            # establish encoding
    srs.ImportFromEPSG(4326)                # WGS84 lat/long (in degrees)
    dst_ds.SetGeoTransform(geotransform)    # specify coords
    dst_ds.SetProjection(srs.ExportToWkt())  # export coords to the file
    # image uses cartesian coordinates, swap to graphics coordinates
    # which means to invert Y axis
    img = np.flip(image, (0))
    dst_ds.GetRasterBand(1).WriteArray(img[:, :, 0])
    dst_ds.GetRasterBand(2).WriteArray(img[:, :, 1])
    dst_ds.GetRasterBand(3).WriteArray(img[:, :, 2])
    dst_ds.FlushCache()
