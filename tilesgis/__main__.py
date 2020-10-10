import logging

from osgeo import gdal
from osgeo import osr
import numpy as np

from tilesgis.types import (
    ExtentDegrees, OSMRelation,
    OSMWay,
)
from tilesgis.parse_osm_xml import xml_to_map_obj
from tilesgis.database_extract import data_from_extent
from tilesgis.draw_helpers import map_to_image

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


def asphalt_way_callback(w: OSMWay):
    if w.attributes is None:
        return
    if w.attributes.get('surface') == 'asphalt':
        return (128, 128, 128)


def any_way_callback(w: OSMWay):
    if w.attributes is not None:
        logger.info(w.attributes)
    return (250, 250, 250)


def any_rel_callback(r: OSMRelation):
    return (250, 250, 250)


if __name__ == '__main__':
    # this cover most of Berlin, takes 5 minutes
    # e = ExtentDegrees(
    #     latmin=52.4650,
    #     latmax=52.5805,
    #     lonmin=13.2911,
    #     lonmax=13.5249
    # )
    # d = data_from_extent(e)
    # img = asphalt_map(d, e)
    # save_to_geoTIFF(e, img, 'all_berlin.db.asphalt.tif')

    way_callback = any_way_callback

    osm_name = 'museum_insel_berlin.osm'
    xml_data, extent = xml_to_map_obj(osm_name)
    xml_img = map_to_image(extent, xml_data, way_callback=way_callback, relation_callback=any_rel_callback)
    save_to_geoTIFF(extent, xml_img, 'image_from_xml.tif')

    db_data = data_from_extent(extent)
    db_img = map_to_image(extent, db_data, way_callback=way_callback, relation_callback=any_rel_callback)
    save_to_geoTIFF(extent, db_img, 'image_from_db.tif')

    # for osm_name in ['new_york_park.osm', 'sample.osm', 'museum_insel_berlin.osm']:
    #     d, e = xml_to_map_obj(osm_name)
    #     img = asphalt_map(d, e)
    #     save_to_geoTIFF(e, img, osm_name + '.asphalt.tif')

    #     d2 = data_from_extent(e)
    #     img2 = asphalt_map(d2, e)
    #     save_to_geoTIFF(e, img2, osm_name + '.db.asphalt.tif')
