import logging
import random
from typing import Tuple

from osgeo import gdal
from osgeo import osr
import numpy as np
from PIL import Image, ImageDraw

from tilesgis.types import (
    AreaData,
    ExtentDegrees,
)
from tilesgis.parse_osm_xml import xml_to_map_obj

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
)

logger = logging.getLogger(__name__)


def save_to_geoTIFF(bbox: ExtentDegrees, image: np.ndarray, fname: str):
    nx, ny = image.shape[:2]
    # this is because the image is distorted if not square
    assert nx == ny
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
    dst_ds.GetRasterBand(1).WriteArray(img[:, :,  0])
    dst_ds.GetRasterBand(2).WriteArray(img[:, :,  1])
    dst_ds.GetRasterBand(3).WriteArray(img[:, :,  2])
    dst_ds.FlushCache()


def coord_to_pixel(lat: float, lon: float, height: float, width: float, extent: ExtentDegrees) -> Tuple[float, float]:
    """Convert lat/lon coordinate to a pixel coordinate for a given area.

    NOTE: this assumes the extent is very small, enough to not introduce errors
    due to curvature. For this project is usually no bigger than a few blocks,
    but a city should be fine too.
    """
    x = (lon - extent.lonmin) * width / (extent.lonmax - extent.lonmin)
    y = (lat - extent.latmin) * height / (extent.latmax - extent.latmin)

    return x, y


def asphalt_map(data: AreaData, extent: ExtentDegrees) -> np.ndarray:
    """Calculate the image with ways within the given extent."""
    img = Image.new('RGB', (800, 800), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    asphalt_ways = []
    for w in data.ways.values():
        if w.attributes is None:
            continue
        if w.attributes.get('surface') == 'asphalt':
            asphalt_ways.append(w.nodes)

    for way in asphalt_ways:
        red = random.randint(1, 250)
        green = random.randint(1, 250)
        blue = random.randint(1, 250)
        for id1, id2 in zip(way, way[1:]):
            n1 = data.nodes.get(id1)
            n2 = data.nodes.get(id2)
            if n1 is None or n2 is None:
                continue
            # now n1 and n2 are two nodes connected by asphalt
            x1, y1 = coord_to_pixel(n1.lat, n1.lon, img.size[0], img.size[1], extent)
            x2, y2 = coord_to_pixel(n2.lat, n2.lon, img.size[0], img.size[1], extent)
            draw.line((x1, y1, x2, y2), fill=(red, green, blue))  # type: ignore

    return np.array(img)


if __name__ == '__main__':
    for osm_name in ['new_york_park.osm', 'sample.osm']:
        d, e = xml_to_map_obj(osm_name)
        img = asphalt_map(d, e)
        save_to_geoTIFF(e, img, osm_name + '.asphalt.tif')
