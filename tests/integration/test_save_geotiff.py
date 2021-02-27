import numpy as np

from geocrazy.draw_helpers import save_to_geoTIFF
from geocrazy.parse_osm_xml import xml_to_map_obj


def test_save_geotiff(tmpdir):
    _features, extent = xml_to_map_obj("tests/sampledata/museum_insel_berlin.osm")
    target_file = tmpdir.join("blabla.tiff")
    save_to_geoTIFF(extent, np.ndarray((100, 100, 3)), str(target_file))
    assert len(tmpdir.listdir()) == 1
    assert target_file.size() > 20_000
    # TODO how to check that the stored coordinates are OK?
    # right now, this is validated visually by importing in QGIS
