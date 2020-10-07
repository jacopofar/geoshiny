from os import environ
from typing import Dict, List, Tuple

import psycopg2
from psycopg2.extras import NamedTupleCursor

from tilesgis.types import AreaData, OSMNode, ExtentDegrees, OSMRelation, OSMWay, RelMemberType

# TODO now it opens a connection every time, but here it's not a problem


def _get_connection():
    return psycopg2.connect(dsn=environ['PGIS_CONN_STR'])


# TODO once the code to get ways is ready, nodes can be retrieved from ways
# without the margin workaround

def nodes_in_extent(extent: ExtentDegrees) -> Dict[int, OSMNode]:
    retval = {}
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                '''SELECT
                    n.id, n.lat, n.lon, p.*
                FROM planet_osm_nodes n
                LEFT JOIN planet_osm_point p
                    ON p.osm_id = n.id
                WHERE
                    lat >= %(latmin)s
                    AND lat <= %(latmax)s
                    AND lon >= %(lonmin)s
                    AND lon <= %(lonmax)s''',
                extent.as_e7_dict())
            for row in cur:
                retval[row.id] = OSMNode(
                    lat=row.lat / 10 ** 7,
                    lon=row.lon / 10 ** 7,
                    attributes={
                        k: v
                        for (k, v) in row._asdict().items()
                        if v is not None and k not in ('lat', 'lon', 'id', 'osm_id', 'way')
                    },
                    )
    conn.close()
    return retval


def ways_including_nodes(node_ids: List[int]) -> Dict[int, OSMWay]:
    """Retrieve the ways that include at least one of the given nodes.

    Notice that ways can and likely will overlap to the extent nodes are from.
    If for example a building is only partially in an extent the corresponding
    way will be retrieved but it will include nodes that are part of the
    building but not of the nodes.

    To integrate these nodes, use `add_missing_nodes`
    """
    if len(node_ids) == 0:
        return {}
    retval = {}
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                '''SELECT
                    id, nodes, tags
                FROM planet_osm_ways w
                WHERE
                    nodes && array[%(node_ids)s]::bigint[]''',
                dict(node_ids=node_ids))
            for row in cur:
                retval[row.id] = OSMWay(
                    nodes=row.nodes,
                    attributes=dict(zip(row.tags[::2], row.tags[1::2])) if row.tags is not None else None
                )

    conn.close()
    return retval


def _integrate_missing_nodes_by_ids(missing_nodes: Tuple, nodes: Dict[int, OSMNode]) -> None:
    if len(missing_nodes) == 0:
        return
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                '''SELECT
                    n.id, n.lat, n.lon, p.*
                FROM planet_osm_nodes n
                LEFT JOIN planet_osm_point p
                    ON p.osm_id = n.id
                WHERE
                    n.id IN %(node_ids)s
                ''',
                dict(node_ids=tuple(missing_nodes))
            )
            for row in cur:
                nodes[row.id] = OSMNode(
                    lat=row.lat / 10 ** 7,
                    lon=row.lon / 10 ** 7,
                    attributes={
                        k: v
                        for (k, v) in row._asdict().items()
                        if v is not None and k not in ('lat', 'lon', 'id', 'osm_id', 'way')
                    },
                    )
    conn.close()


def add_missing_nodes(nodes: Dict[int, OSMNode], ways: Dict[int, OSMWay]) -> None:
    """Integrate a list of nodes with ones missing from ways.

    This modifies the nodes dict by adding nodes to it, all the ones present
    in the given ways but not already in the nodes.

    This is used to get nodes of features only partially in an extent.
    """
    missing_nodes = set()
    for w in ways.values():
        for n_id in w.nodes:
            if n_id not in nodes:
                missing_nodes.add(n_id)

    _integrate_missing_nodes_by_ids(tuple(missing_nodes), nodes)


def rels_including_ways(way_ids: List[int]) -> Dict[int, OSMRelation]:
    """Retrieve the relations that include at least one of the given ways.

    Notice that just as for nodes in ways, a relations overlapping with an
    extent edge can contain ways that are outside the extent itself.
    Also note that a relation can include ways AND nodes
    """
    if len(way_ids) == 0:
        return {}
    retval = {}
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                '''SELECT
                    id, members, tags
                FROM planet_osm_rels
                WHERE
                    parts && array[%(way_ids)s]::bigint[]''',
                dict(way_ids=way_ids))
            for row in cur:
                members = []
                for wdesc, wtype in zip(row.members[::2], row.members[1::2]):
                    members.append((
                        RelMemberType.WAY if wdesc.startswith('w') else RelMemberType.NODE,
                        int(wdesc[1:]),
                        wtype
                    ))

                retval[row.id] = OSMRelation(
                    members=members,
                    attributes=(
                        dict(zip(row.tags[::2], row.tags[1::2]))
                        if row.tags is not None
                        else None
                        )
                )

    conn.close()
    return retval


def add_missing_nodes_and_ways(
    nodes: Dict[int, OSMNode],
    ways: Dict[int, OSMWay],
    rels: Dict[int, OSMRelation],
        ) -> None:
    """Integrate a list of nodes and ways with ones missing from rels.

    Just as it happens with nodes and ways, a relation can contain nodes and
    ways that are both inside and outside an extent.
s
    So to draw a map one has to "peek" outside the area.

    This function takes a dictionary of ways and nodes and adds whatever is
    needed to define the relations.
    """
    missing_nodes_ids = set()
    missing_ways_ids = set()
    for r in rels.values():
        for rtype, m_id, _mtype in r.members:
            if rtype == RelMemberType.NODE:
                if m_id not in nodes:
                    missing_nodes_ids.add(m_id)
            if rtype == RelMemberType.WAY:
                if m_id not in ways:
                    missing_ways_ids.add(m_id)
    print(f'missing ways {len(missing_ways_ids)}')
    print(f'missing nodes {len(missing_nodes_ids)}')

    if len(missing_ways_ids) > 0:
        with _get_connection() as conn:
            with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
                cur.execute(
                    '''SELECT
                        id, nodes, tags
                    FROM planet_osm_ways w
                    WHERE
                        id IN %(way_ids)s''',
                    dict(way_ids=tuple(missing_ways_ids)))
                for row in cur:
                    ways[row.id] = OSMWay(
                        nodes=row.nodes,
                        attributes=(
                            dict(zip(row.tags[::2], row.tags[1::2]))
                            if row.tags is not None
                            else None
                            )
                    )
        conn.close()

    _integrate_missing_nodes_by_ids(tuple(missing_nodes_ids), nodes)
    # now ways and nodes are added
    # but some of these ways may not have all the needed nodes, so fix it
    add_missing_nodes(nodes, ways)


def data_from_extent(extent: ExtentDegrees) -> AreaData:
    nodes = nodes_in_extent(extent)
    ways = ways_including_nodes(list(nodes.keys()))
    rels = rels_including_ways(list(ways.keys()))
    add_missing_nodes_and_ways(nodes, ways, rels)

    return AreaData(
        nodes=nodes,
        ways=ways,
        relations=rels,
    )
