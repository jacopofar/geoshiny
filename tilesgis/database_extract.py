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

def nodes_in_extent(extent: ExtentDegrees, margin: float = 0.33) -> Dict[int, OSMNode]:
    """Retrieves the OSM Nodes in an extend, plus some margin.

    The margin is quite tricky. If you export an XML from the OSM web
    interface it contains nodes that are outside the bound.
    This happens because they are part of some way that is partially inside
    the extent, for example a building. However it doesn't apply for *all*
    such ways, and I couldn't figure out the criteria and how to implement it
    without huge queries.
    So, as a simple workaround, this function gives nodes that are a bit
    outside the extent.

    Parameters
    ----------
    margin : float
        How much to enlarge the extent to retrieve. 0.33 means 33% larger in
        all directions
    """
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
                extent.enlarged(margin).as_e7_dict())
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
                print(row.tags)
                retval[row.id] = OSMWay(
                    nodes=row.nodes,
                    attributes=dict(zip(row.tags[::2], row.tags[1::2])) if row.tags is not None else None
                )

    conn.close()
    return retval
