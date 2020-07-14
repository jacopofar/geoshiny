import logging

from osgeo import gdal
from osgeo import osr
import numpy as np

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
)

logger = logging.getLogger(__name__)


def saveToGeoTIFF(latmin: float, latmax: float, lonmin: float, lonmax: float, image: np.ndarray, fname: str):
    nx, ny = image.shape[:2]
    # this is because the image is distorted if not square
    assert nx == ny
    xres = (lonmax - lonmin) / nx
    yres = (latmax - latmin) / ny
    geotransform = (lonmin, xres, 0, latmax, 0, -yres)

    dst_ds = gdal.GetDriverByName('GTiff').Create(fname, ny, nx, 3, gdal.GDT_Byte)

    srs = osr.SpatialReference()            # establish encoding
    srs.ImportFromEPSG(4326)                # WGS84 lat/long (in degrees)
    dst_ds.SetGeoTransform(geotransform)    # specify coords
    dst_ds.SetProjection(srs.ExportToWkt())  # export coords to the file
    dst_ds.GetRasterBand(1).WriteArray(image[:, :, 0])   # write r-band to the raster
    dst_ds.GetRasterBand(2).WriteArray(image[:, :, 1])   # write g-band to the raster
    dst_ds.GetRasterBand(3).WriteArray(image[:, :, 2])   # write b-band to the raster
    dst_ds.FlushCache()


if __name__ == '__main__':
    from random import randint
    image = np.zeros((10, 30, 3), dtype=np.uint8)
    for x in range(0, image.shape[0]):
        for y in range(0, image.shape[1]):
            image[x][y][0] = randint(1, 255)
            image[x][y][1] = randint(1, 255)
            image[x][y][2] = randint(1, 255)
    # coordinates for the Bresso airport landing strip, used here as a reference
    saveToGeoTIFF(45.5331, 45.5465, 9.1986, 9.2056, image, 'newFile.tif')
