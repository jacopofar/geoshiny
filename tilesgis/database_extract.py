from os import environ
import logging
from typing import Dict, Tuple

import psycopg2
from psycopg2.extras import NamedTupleCursor

from tilesgis.types import AreaData, OSMNode, ExtentDegrees, OSMRelation, OSMWay, RelMemberType

# TODO now it opens a connection every time, but here it's not a problem


logger = logging.getLogger(__name__)


def _get_connection():
    return psycopg2.connect(dsn=environ['PGIS_CONN_STR'])


def _integrate_missing_nodes_by_ids(missing_nodes: Tuple, nodes: Dict[int, OSMNode]) -> None:
    logger.debug(f'Retrieving and adding {len(missing_nodes)}')
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


def add_missing_nodes_and_ways(
    nodes: Dict[int, OSMNode],
    ways: Dict[int, OSMWay],
    rels: Dict[int, OSMRelation],
        ) -> None:
    """Integrate a list of nodes and ways with ones missing from rels.

    Just as it happens with nodes and ways, a relation can contain nodes and
    ways that are both inside and outside an extent.

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
    logger.debug(
        f'Found {len(missing_ways_ids)} ways and {len(missing_nodes_ids)} nodes'
        ' missing')
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
    logger.debug('Ways integrated, now adding the nodes')

    _integrate_missing_nodes_by_ids(tuple(missing_nodes_ids), nodes)

    # now ways and nodes are added
    # but some of these ways may not have all the needed nodes, so fix it
    add_missing_nodes(nodes, ways)


def data_from_extent(extent: ExtentDegrees) -> AreaData:
    nodes = nodes_in_extent(extent)
    ways = ways_in_extent(extent)
    rels = relations_in_extent(extent)
    add_missing_nodes_and_ways(nodes, ways, rels)

    return AreaData(
        nodes=nodes,
        ways=ways,
        relations=rels,
    )


def nodes_in_extent(extent: ExtentDegrees) -> Dict[int, OSMNode]:
    retval = {}
    logger.debug(f'Searching for nodes in extent {extent}')
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                '''SELECT
                        n.id,
                        n.lat,
                        n.lon,
                        p.*
                    FROM
                        planet_osm_nodes n
                            LEFT JOIN planet_osm_point p
                                    ON p.osm_id = n.id
                    WHERE
                            p.way && st_makeenvelope(
                                %(lonmin)s, %(latmin)s, %(lonmax)s, %(latmax)s
                                , 3857);''',
                extent.as_epsg3857())
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
    logger.debug(f'Found {len(retval)} nodes')
    return retval


def ways_in_extent(extent: ExtentDegrees) -> Dict[int, OSMWay]:
    """Retrieve the ways in a given extent.

    Ways correspond to entries in the line, polygon and roads tables with
    positive ids. For example a road with id=5 is relation with id=5
    """
    retval = {}
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                '''SELECT
                        id,
                        nodes,
                        tags,
                        ST_AsGeoJSON(ST_Transform(l.way, 4326)) AS geojson
                    FROM planet_osm_ways w

                    JOIN planet_osm_line l
                            ON l.osm_id = w.id
                    WHERE
                        l.way && st_makeenvelope(
                        %(lonmin)s, %(latmin)s, %(lonmax)s, %(latmax)s
                        , 3857)

                    UNION ALL

                    SELECT
                        id,
                        nodes,
                        tags,
                        ST_AsGeoJSON(ST_Transform(r.way, 4326)) AS geojson
                    FROM planet_osm_ways w

                            JOIN planet_osm_roads r
                                ON r.osm_id = w.id
                    WHERE
                            r.way && st_makeenvelope(
                            %(lonmin)s, %(latmin)s, %(lonmax)s, %(latmax)s
                            , 3857)

                    UNION ALL

                    SELECT
                        id,
                        nodes,
                        tags,
                        ST_AsGeoJSON(ST_Transform(p.way, 4326)) AS geojson
                    FROM planet_osm_ways w

                            JOIN planet_osm_polygon p
                                ON p.osm_id = w.id
                    WHERE
                            p.way && st_makeenvelope(
                            %(lonmin)s, %(latmin)s, %(lonmax)s, %(latmax)s
                            , 3857)
                        ''',
                extent.as_epsg3857())
            for row in cur:
                retval[row.id] = OSMWay(
                    nodes=row.nodes,
                    attributes=(
                        dict(zip(row.tags[::2], row.tags[1::2]))
                        if row.tags is not None
                        else None),
                    geoJSON=row.geojson
                )

    conn.close()
    logger.debug(f'Found {len(retval)} matching ways')

    return retval


def relations_in_extent(extent: ExtentDegrees) -> Dict[int, OSMRelation]:
    """Retrieve the relations in a given extent.

    Relations correspond to entries in the line, polygon and roads tables with
    negative ids. For example a road with id -15 is relation with id 15
    """
    retval = {}
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            # TODO check that ids are positive, all these 3 tables can have negative ids!
            # maybe sometimes we need to change the sign
            cur.execute(
                '''SELECT
                        id,
                        members,
                        tags,
                        ST_AsGeoJSON(ST_Transform(l.way, 4326)) AS geojson
                    FROM planet_osm_rels rel

                    JOIN planet_osm_line l
                            ON l.osm_id = -rel.id
                    WHERE
                        l.way && st_makeenvelope(
                        %(lonmin)s, %(latmin)s, %(lonmax)s, %(latmax)s
                        , 3857)

                    UNION ALL

                    SELECT
                        id,
                        members,
                        tags,
                        ST_AsGeoJSON(ST_Transform(r.way, 4326)) AS geojson
                    FROM planet_osm_rels rel

                            JOIN planet_osm_roads r
                                ON r.osm_id = -rel.id
                    WHERE
                            r.way && st_makeenvelope(
                            %(lonmin)s, %(latmin)s, %(lonmax)s, %(latmax)s
                            , 3857)

                    UNION ALL

                    SELECT
                        id,
                        members,
                        tags,
                        ST_AsGeoJSON(ST_Transform(p.way, 4326)) AS geojson
                    FROM planet_osm_rels rel

                            JOIN planet_osm_polygon p
                                ON p.osm_id = -rel.id
                    WHERE
                            p.way && st_makeenvelope(
                            %(lonmin)s, %(latmin)s, %(lonmax)s, %(latmax)s
                            , 3857)
                        ''',
                extent.as_epsg3857())
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
                        ),
                    geoJSON=row.geojson,
                )

    conn.close()
    logger.debug(f'Found {len(retval)} matching relations')
    return retval
