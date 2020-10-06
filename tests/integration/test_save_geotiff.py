import numpy as np

from tilesgis.__main__ import save_to_geoTIFF, xml_to_map_obj


def test_save_geotiff(tmpdir):
    _features, extent = xml_to_map_obj('tests/sampledata/museum_insel_berlin.osm')
    target_file = tmpdir.join('blabla.tiff')
    save_to_geoTIFF(extent, np.ndarray((100, 100, 3)), str(target_file))
    assert len(tmpdir.listdir()) == 1
    assert target_file.size() > 20_000
