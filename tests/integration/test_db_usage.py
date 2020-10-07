from tilesgis.types import ExtentDegrees
from tilesgis.database_extract import (
    add_missing_nodes,
    add_missing_nodes_and_ways,
    data_from_extent,
    nodes_in_extent,
    rels_including_ways,
    ways_including_nodes,
)


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
    assert len(nodes) > 1000
    assert 289032659 in nodes
    n = nodes[289032659]
    assert n.attributes == {'addr_housenumber': '13'}


def test_get_ways_with_nodes():
    ways = ways_including_nodes([
        289032659,
        848523542
    ])
    assert len(ways) == 5
    assert set(ways.keys()) == set([
        4566442,
        26382762,
        48145154,
        66514420,
        170077664,
    ])

    assert 66514420 in ways
    w = ways[66514420]
    assert w.attributes['name'] == 'Märkisches Ufer'
    assert w.attributes['bicycle'] == 'yes'


def test_add_missing_nodes():
    nodes = nodes_in_extent(
        ExtentDegrees(
            latmin=52.5130200,
            lonmin=13.4087500,
            latmax=52.5160500,
            lonmax=13.4154700,
            )
        )
    original_node_count = len(nodes)
    ways = ways_including_nodes(list(nodes.keys()))

    add_missing_nodes(nodes, ways)
    assert len(nodes) > original_node_count


def test_get_relations_with_ways():
    rels = rels_including_ways([
        4566442,
        26382762,
        48145154,
        66514420,
        170077664,
    ])
    assert len(rels) == 1
    assert 28130 in rels
    r = rels[28130]
    assert r.attributes['name'] == 'Senatsverwaltung für Finanzen und Technisches Finanzamt'


def test_add_missing_nodes_and_ways():
    nodes = nodes_in_extent(
        ExtentDegrees(
            latmin=52.50319,
            latmax=52.50507,
            lonmin=13.22676,
            lonmax=13.23066,
            )
        )
    original_node_count = len(nodes)
    ways = ways_including_nodes(list(nodes.keys()))
    original_ways_count = len(ways)
    rels = rels_including_ways(list(ways.keys()))

    add_missing_nodes_and_ways(nodes, ways, rels)

    assert len(nodes) > original_node_count
    assert len(ways) > original_ways_count


def test_complete_retrieval():
    extent = ExtentDegrees(
        latmin=52.50319,
        latmax=52.50507,
        lonmin=13.22676,
        lonmax=13.23066,
        )
    data = data_from_extent(extent)
    direct_nodes = nodes_in_extent(extent)
    # the exact number changes overe time...
    assert len(data.nodes) > len(direct_nodes)
    assert len(data.nodes) > 100
    assert len(data.ways) > 100
    assert len(data.relations) > 5
