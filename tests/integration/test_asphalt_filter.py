from copy import deepcopy

import numpy as np

from tilesgis.__main__ import asphalt_map, xml_to_map_obj


def test_save_geotiff(tmpdir):
    map_data, extent = xml_to_map_obj('tests/sampledata/museum_insel_berlin.osm')
    img = asphalt_map(map_data, extent)

    assert img.shape == (800, 800, 3)
    # just check it's not totally black, the value is a lower bound
    # it's random and around 1M
    assert np.sum(img) > 10_000

    # remove the asphalt, ensure the result it is indeed empty
    map_data_stripped = deepcopy(map_data)
    for way in map_data_stripped.ways.values():
        if way.attributes is not None:
            way.attributes['surface'] = 'not asphalt'
    img_stripped = asphalt_map(map_data_stripped, extent)

    assert img_stripped.shape == (800, 800, 3)
    assert np.sum(img_stripped) == 0.0

