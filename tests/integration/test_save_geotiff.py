import numpy as np
import pytest

from geoshiny.draw_helpers import save_to_geoTIFF
from geoshiny.types import ExtentDegrees

# this test requires the GDAL dependency
@pytest.mark.xfail
def test_save_geotiff(tmpdir):
    extent = ExtentDegrees(
        latmin=40.78040,
        latmax=40.78280,
        lonmin=-73.96050,
        lonmax=-73.96350,
    )
    target_file = tmpdir.join("blabla.tiff")
    save_to_geoTIFF(extent, np.ndarray((100, 100, 3)), str(target_file))
    assert len(tmpdir.listdir()) == 1
    assert target_file.size() > 20_000
    # TODO how to check that the stored coordinates are OK?
    # right now, this is validated visually by importing in QGIS
