import pytest

from geoshiny.types import ExtentDegrees
from geoshiny.parse_osm_xml import xml_to_map_obj


@pytest.mark.skip(reason="This has to be reimplemented or just removed")
def test_xml_is_parsed():
    features, extent = xml_to_map_obj("tests/sampledata/museum_insel_berlin.osm")
    assert extent == ExtentDegrees(
        latmin=52.51302, latmax=52.51605, lonmin=13.40875, lonmax=13.41547
    )
    assert len(features.nodes) == 2030
    assert len(features.ways) == 200
    assert len(features.relations) == 49
