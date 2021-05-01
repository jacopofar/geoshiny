import re

from geoshiny.database_extract import build_tags_join_query


def test_ebuild_tags_join_query():
    sql = build_tags_join_query("schema_name", ("some_polygon",))
    sql = sql.replace("\n", " ")
    sql = re.sub(" +", " ", sql).strip()
    assert sql == (
        "SELECT schema_name.some_polygon.osm_id, geom, tags FROM "
        "schema_name.some_polygon JOIN schema_name.tags ON "
        "abs(schema_name.some_polygon.osm_id) = schema_name.tags.osm_id WHERE "
        "geom && st_makeenvelope($1, $2, $3, $4, 3857)"
    )

    sql = build_tags_join_query("eee", ("bla", "blip"))
    sql = sql.replace("\n", " ")
    sql = re.sub(" +", " ", sql).strip()
    assert sql == (
        "SELECT eee.bla.osm_id, geom, tags FROM eee.bla JOIN eee.tags ON "
        "abs(eee.bla.osm_id) = eee.tags.osm_id WHERE geom && "
        "st_makeenvelope($1, $2, $3, $4, 3857) UNION ALL SELECT "
        "eee.blip.osm_id, geom, tags FROM eee.blip JOIN eee.tags ON "
        "abs(eee.blip.osm_id) = eee.tags.osm_id WHERE geom && "
        "st_makeenvelope($1, $2, $3, $4, 3857)"
    )
