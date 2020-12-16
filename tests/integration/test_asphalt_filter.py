from copy import deepcopy

import numpy as np
import pytest

from tilesgis.parse_osm_xml import xml_to_map_obj
from tilesgis.types import OSMWay
from tilesgis.draw_helpers import figure_to_numpy, data_to_representation, representations_to_figure


@pytest.mark.skip(reason='shape generation from XML is not implemented yet')
def test_asphalt_filter(tmpdir):
    def asphalt_data(w: OSMWay):
        if w.attributes.get('surface') == 'asphalt':
            return dict(asphalt=True)

    def asphalt_repr(d):
        if d.get('asphalt'):
            return dict(facecolor='grey')

    map_data, extent = xml_to_map_obj('tests/sampledata/museum_insel_berlin.osm')
    reprs = data_to_representation(map_data, entity_callback=asphalt_repr)
    fig = representations_to_figure(reprs, extent, asphalt_repr, figsize=800)

    img = figure_to_numpy(fig)
    assert img.shape == (800, 800, 4)
    # just check it's not totally black, the value is a lower bound
    # it's random and around 1M
    assert np.sum(img) > 10_000

    # remove the asphalt, ensure the result it is indeed empty
    map_data_stripped = deepcopy(map_data)
    for way in map_data_stripped.ways.values():
        if way.attributes is not None:
            way.attributes['surface'] = 'not asphalt'

    reprs_stripped = data_to_representation(map_data_stripped, entity_callback=asphalt_repr)
    fig_stripped = representations_to_figure(reprs_stripped, extent, asphalt_repr, figsize=800)
    img_stripped = figure_to_numpy(fig_stripped)

    assert img_stripped.shape == (800, 800, 4)
    assert np.sum(img_stripped) == 0.0

