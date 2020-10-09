from copy import deepcopy

import numpy as np

from tilesgis.__main__ import xml_to_map_obj
from tilesgis.types import OSMWay
from tilesgis.draw_helpers import map_to_image


def test_save_geotiff(tmpdir):
    def asphalt_way_callback(w: OSMWay):
        if w.attributes is None:
            return
        if w.attributes.get('surface') == 'asphalt':
            return (128, 128, 128)

    map_data, extent = xml_to_map_obj('tests/sampledata/museum_insel_berlin.osm')
    img = map_to_image(extent, map_data, way_callback=asphalt_way_callback)

    assert img.shape == (800, 800, 3)
    # just check it's not totally black, the value is a lower bound
    # it's random and around 1M
    assert np.sum(img) > 10_000

    # remove the asphalt, ensure the result it is indeed empty
    map_data_stripped = deepcopy(map_data)
    for way in map_data_stripped.ways.values():
        if way.attributes is not None:
            way.attributes['surface'] = 'not asphalt'
    img_stripped = map_to_image(extent, map_data_stripped, way_callback=asphalt_way_callback)

    assert img_stripped.shape == (800, 800, 3)
    assert np.sum(img_stripped) == 0.0

