from tilesgis.types import ExtentDegrees
from tilesgis.database_extract import nodes_in_extent, ways_including_nodes


def test_nodes_in_extent():
    nodes = nodes_in_extent(
        ExtentDegrees(
            latmin=52.5130200,
            lonmin=13.4087500,
            latmax=52.5160500,
            lonmax=13.4154700,
            )
        )
    # meh, no fixtures here, data may change :/
    assert len(nodes) > 2000
    assert 289032659 in nodes
    n = nodes[289032659]
    assert n.attributes == {'addr_housenumber': '13'}


def test_get_ways_with_nodes():
    ways = ways_including_nodes([
        289032659,
        848523542
    ])
    assert len(ways) == 5

    assert 66514420 in ways
    w = ways[66514420]
    assert w.attributes['name'] == 'Märkisches Ufer'
    assert w.attributes['bicycle'] == 'yes'
