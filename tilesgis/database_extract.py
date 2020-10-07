from os import environ
from typing import Dict, List

import psycopg2
from psycopg2.extras import NamedTupleCursor

from tilesgis.types import OSMNode, ExtentDegrees, OSMWay

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
