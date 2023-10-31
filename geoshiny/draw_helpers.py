from contextlib import contextmanager
import json
import logging
from io import TextIOWrapper
from typing import Dict, Callable, Iterable, List, Optional, Tuple, Union

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import numpy as np
from numpy import asarray, concatenate, ones
from shapely.geometry.base import BaseGeometry
from shapely.geometry import mapping, shape

from geoshiny.types import ExtentDegrees, Geometry2DStyle

logger = logging.getLogger(__name__)

# NOTE these three classes are from https://github.com/benjimin/descartes/blob/master/descartes/patch.py
# it's basically the only code I could find that does this -_-


class Polygon:
    # Adapt Shapely or GeoJSON/geo_interface polygons to a common interface
    def __init__(self, context):
        if hasattr(context, "interiors"):
            self.context = context
        else:
            self.context = getattr(context, "__geo_interface__", context)

    @property
    def geom_type(self):
        return getattr(self.context, "geom_type", None) or self.context["type"]

    @property
    def exterior(self):
        return getattr(self.context, "exterior", None) or self.context["coordinates"][0]

    @property
    def interiors(self):
        value = getattr(self.context, "interiors", None)
        if value is None:
            value = self.context["coordinates"][1:]
        return value


def to_polygon_path(polygon):
    """Constructs a compound matplotlib path from a Shapely or GeoJSON-like
    geometric object"""
    this = Polygon(polygon)
    assert this.geom_type == "Polygon"

    def coding(ob):
        # The codes will be all "LINETO" commands, except for "MOVETO"s at the
        # beginning of each subpath
        n = len(getattr(ob, "coords", None) or ob)
        vals = ones(n, dtype=Path.code_type) * Path.LINETO
        vals[0] = Path.MOVETO
        return vals

    vertices = concatenate(
        [asarray(this.exterior)[:, :2]] + [asarray(r)[:, :2] for r in this.interiors]
    )
    codes = concatenate([coding(this.exterior)] + [coding(r) for r in this.interiors])
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


def coord_to_pixel(
    lat: float, lon: float, height: float, width: float, extent: ExtentDegrees
) -> Tuple[float, float]:
    """Convert lat/lon coordinate to a pixel coordinate for a given area.

    NOTE: this assumes the extent is very small, enough to not introduce errors
    due to curvature. For this project is usually no bigger than a city.
    """
    x = (lon - extent.lonmin) * width / (extent.lonmax - extent.lonmin)
    y = (lat - extent.latmin) * height / (extent.latmax - extent.latmin)

    return x, y


def _representation_iterator(
    data,
    entity_callback: Callable[[int, BaseGeometry, dict], Optional[dict]],
):
    for (osm_id, geom, tags) in data:
        representation = entity_callback(osm_id, geom, tags)
        if representation is not None:
            yield (osm_id, geom, representation)


@contextmanager
def _read_file(target_file: Union[str, TextIOWrapper]):
    if isinstance(target_file, str):
        with open(target_file, "r") as fh:
            yield fh
    elif isinstance(target_file, TextIOWrapper):
        yield target_file
    else:
        raise TypeError(f"Invalid type {type(target_file)}")


@contextmanager
def _write_file(target_file: Union[str, TextIOWrapper]):
    if isinstance(target_file, str):
        with open(target_file, "w") as fh:
            yield fh
    elif isinstance(target_file, TextIOWrapper):
        yield target_file
    else:
        raise TypeError(f"Invalid type {type(target_file)}")


def data_to_representation(
    data,
    entity_callback: Callable,
) -> Iterable[Tuple[int, BaseGeometry, dict]]:
    yield from _representation_iterator(data, entity_callback)


def data_to_representation_file(
    data,
    target_file: Union[str, TextIOWrapper],
    entity_callback: Callable,
):
    with _write_file(target_file) as fh:
        for osm_id, geom, repr in _representation_iterator(data, entity_callback):
            fh.write(
                json.dumps(
                    dict(
                        osm_id=osm_id,
                        geojson=mapping(geom),
                        representation=repr,
                    )
                )
            )
            fh.write("\n")


def file_to_representation(target_file: Union[str, TextIOWrapper]):
    with _read_file(target_file) as fh:
        for line in fh:
            obj = json.loads(line)
            yield (obj["osm_id"], shape(obj["geojson"]), obj["representation"])


def representation_to_figure(
    representations: Iterable[Tuple[int, BaseGeometry, dict]],
    extent: ExtentDegrees,
    representer: Callable[[int, BaseGeometry, dict], Optional[Geometry2DStyle]],
    figsize: int = 1500,
) -> Figure:

    to_draw = []

    for osm_id, geom, repr in representations:
        res = representer(osm_id, geom, repr)
        if res is None:
            continue

        new_shape = res.shape if res.shape is not None else geom
        to_draw.append((new_shape, res))
    return render_shapes_to_figure(extent, to_draw, figsize)


def render_shapes_to_figure(
    extent: ExtentDegrees,
    to_draw: List[Tuple[BaseGeometry, Geometry2DStyle]],
    figsize: int = 1500,
) -> Figure:
    """Renders arbitrary Shapely geometrical objects to a Figure.

    This is quite ambitious!

    the to_draw argument is a list of Shapely geometrical objects and rules to
    draw them (color, style, etc.)
    """
    fig = Figure(figsize=(5, 5), dpi=figsize / 5, frameon=False)
    ax = fig.add_subplot()
    lonmin, latmin, lonmax, latmax = extent.as_epsg3857()
    ax.set_ylim(latmin, latmax)
    ax.set_xlim(lonmin, lonmax)
    # the total area, used to compare with geometries areas
    total_area = (latmax - latmin) * (lonmax - lonmin)
    # the following lines are the result of an ABSURD amount of attempts
    # I really hope one day matplotlib will become more intuitive ;_;
    ax.set_xmargin(0.0)
    ax.set_ymargin(0.0)
    ax.set_axis_off()

    fig.subplots_adjust(bottom=0)
    fig.subplots_adjust(top=1)
    fig.subplots_adjust(right=1)
    fig.subplots_adjust(left=0)

    for geom, style in to_draw:
        draw_options = style.get_drawing_options()
        label_options = style.get_label_options()
        # the possible types are FeatureCollection, Feature, Point, LineString, MultiPoint,
        # Polygon, MultiLineString, MultiPolygon, and GeometryCollection
        # however I found only these three so far
        if label_options is not None:
            min_label_area_ratio = style.min_label_area_ratio
            geom_size = geom.area
            if (
                min_label_area_ratio is None
                or geom_size / total_area > min_label_area_ratio
            ):
                x, y = geom.centroid.xy
                x = x[0]
                y = y[0]
                ax.text(
                    x,
                    y,
                    label_options["text"],
                    **{k: v for k, v in label_options.items() if k != "text"},
                )
        try:
            if geom.type == "LineString":
                x, y = geom.xy
                ax.plot(x, y, **draw_options)
                continue

            if geom.type == "Polygon":
                patch = create_polygon_patch(geom, **draw_options)
                ax.add_patch(patch)
                continue

            if geom.type == "MultiPolygon":
                for sub_geom in geom.geoms:
                    patch = create_polygon_patch(sub_geom, **draw_options)
                    ax.add_patch(patch)
                continue

            if geom.type == "Point":
                x, y = geom.xy
                ax.scatter(x, y, **draw_options)
                continue

            raise ValueError(f"Cannot draw type {geom.type}")

        except AttributeError:
            logger.exception(
                f"Error drawing, will skip {geom}, options: {draw_options}"
            )

    return fig


def figure_to_numpy(fig: Figure) -> np.ndarray:
    """Render a matplotlib Figure to a Numpy array."""
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    buf = canvas.buffer_rgba()
    # convert to a NumPy array, flip to deal with the y axis
    return np.flipud(np.asarray(buf))
