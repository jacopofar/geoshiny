from os import environ
from functools import lru_cache
import json
import logging
from typing import AsyncGenerator, Callable, List, Optional, Tuple

import asyncpg
import shapely.geometry
import shapely.wkb
from shapely.geometry.base import BaseGeometry

from geoshiny.types import ExtentDegrees

logger = logging.getLogger(__name__)


QUERY_CHUNK_SIZE = 500_000


@lru_cache()
def build_tags_join_query(schema: str, tables: Tuple[str]) -> str:
    """Generate a query to retrieve geometries from multiple tables.

    All the tables have to be in the given schema, and have an
    osm_id and a geom column which contains indexed geometries.

    There is also a tags table containing the tags for each entry.

    This is based on the structure generated by osm2pgsql flex output.
    """
    subs = [
        f"""
        SELECT {schema}.{t}.osm_id, geom, tags
        FROM {schema}.{t} JOIN {schema}.tags
            ON abs({schema}.{t}.osm_id) = {schema}.tags.osm_id
        WHERE
        geom && st_makeenvelope($1, $2, $3, $4, 3857)
        """
        for t in tables
    ]
    return "\n UNION ALL \n ".join(subs)


async def get_connection(dsn: str) -> asyncpg.Connection:
    conn = await asyncpg.connect(dsn=dsn)

    def encode_geometry(geometry):
        if not hasattr(geometry, "__geo_interface__"):
            raise TypeError(
                "{g} does not conform to " "the geo interface".format(g=geometry)
            )
        shape = shapely.geometry.asShape(geometry)
        return shapely.wkb.dumps(shape)

    def decode_geometry(wkb):
        return shapely.wkb.loads(wkb)

    await conn.set_type_codec(
        "geometry",  # also works for 'geography'
        encoder=encode_geometry,
        decoder=decode_geometry,
        format="binary",
    )
    await conn.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )
    return conn


async def geometry_tables(
    conn,
    tables: Optional[List[str]] = None,
    schema: str = "osm",
) -> List[str]:
    if tables is None:
        records = await conn.fetch(
            """
        SELECT
            table_name
        FROM information_schema.columns
        WHERE
            table_schema = $1
        AND column_name = 'geom';
        """,
            schema,
        )
        tables = [r["table_name"] for r in records]

    geom_tables: List[str] = []

    for t in tables:
        full_name = f"{schema}.{t}"
        if t.endswith("point"):
            geom_tables.append(t)
        elif t.endswith("line"):
            geom_tables.append(t)
        elif t.endswith("polygon"):
            geom_tables.append(t)
        else:
            raise ValueError(f"Table {full_name} has no known geometry type")
    return geom_tables


async def raw_data_from_extent(
    extent: ExtentDegrees,
    schema: str = "osm",
    dsn=None,
    tables: Optional[List[str]] = None,
) -> List[asyncpg.Record]:
    if dsn is None:
        dsn = environ["PGIS_CONN_STR"]
    conn = await get_connection(dsn)
    geom_tables = await geometry_tables(conn, tables, schema)

    # TODO return async generators instead?
    # would force the user to use async
    ret = []
    async for r in geoms_in_extent(conn, schema, extent, geom_tables):
        ret.append(r)
    return ret


async def representation_from_extent(
    extent: ExtentDegrees,
    representer: Callable[[int, BaseGeometry, dict], Optional[dict]],
    schema: str = "osm",
    dsn=None,
    tables: Optional[List[str]] = None,
) -> List[Tuple[int, BaseGeometry, dict]]:
    if dsn is None:
        dsn = environ["PGIS_CONN_STR"]
    conn = await get_connection(dsn)
    geom_tables = await geometry_tables(conn, tables, schema)

    # TODO return async generators instead?
    # would force the user to use async
    ret = []
    async for (osm_id, geom, tags) in geoms_in_extent(
        conn, schema, extent, geom_tables
    ):
        representation = representer(osm_id, geom, tags)
        if representation is not None:
            ret.append((osm_id, geom, representation))
    return ret


async def geoms_in_extent(
    conn: asyncpg.Connection, schema: str, extent: ExtentDegrees, tables: List[str]
) -> AsyncGenerator[asyncpg.Record, None]:
    # TODO what is the return type for this?
    # also, subclass the Record or lazily adapt it to something with proper types
    query = build_tags_join_query(schema, tuple(tables))
    # use a cursor and build a list to not stress the DB memory too much
    # later this could be directly returned
    async with conn.transaction():
        async for record in conn.cursor(query, *extent.as_epsg3857()):
            yield record
