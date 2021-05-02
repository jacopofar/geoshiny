import asyncio
import logging
from typing import Optional

# TODO this should not be needed, and makes sense only for the full GDAL install
# what to do with that?
# from geoshiny import import_hell
# # this fixes some weird import issues and raises an error
# import_hell.import_gdal_shapely(wait=False)

from shapely.geometry.base import BaseGeometry

from geoshiny.types import (
    ExtentDegrees,
    ObjectStyle,
)
from geoshiny.database_extract import data_from_extent
from geoshiny.draw_helpers import (
    figure_to_numpy,
    save_to_geoTIFF,
    data_to_representation,
    representation_to_figure,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


def nice_representation(osm_id: int, geom, tags: dict) -> Optional[dict]:
    if tags.get("bicycle") == "designated":
        return dict(path_type="bike")
    if "water" in tags:
        return dict(surface_type="water")

    if tags.get("landuse") == "grass":
        return dict(surface_type="grass")
    if tags.get("leisure") == "park":
        return dict(surface_type="grass")
    if tags.get("natural") == "scrub":
        return dict(surface_type="wild grass")

    if "building" in tags and tags["building"] != "no":
        if "building:levels" not in tags:
            return dict(surface_type="building")
        else:
            try:
                level_num = float(tags["building:levels"])
            except ValueError:
                logger.debug(f"Invalid number of floors: {tags['building:levels']}")
                return dict(surface_type="building")
            return dict(surface_type="building", floors=level_num)
    return None


def nice_renderer(osm_id: int, shape: BaseGeometry, d: dict):
    water_style = ObjectStyle(facecolor="blue", edgecolor="darkblue", linewidth=0.1)
    grass_style = ObjectStyle(facecolor="green", linewidth=0.1)
    wild_grass_style = ObjectStyle(facecolor="darkgreen", linewidth=0.1)

    missing_levels = ObjectStyle(facecolor="red", edgecolor="darkred", linewidth=0.05)
    tall_build = ObjectStyle(facecolor="black", edgecolor="black", linewidth=0.05)
    low_build = ObjectStyle(facecolor="grey", edgecolor="darkgrey", linewidth=0.05)

    bike_path = ObjectStyle(linestyle="dashed", color="yellow", linewidth=0.1)

    if d.get("path_type") == "bike":
        return bike_path

    surface_type = d.get("surface_type")
    if surface_type == "building":
        if "floors" not in d:
            return missing_levels
        else:
            if d["floors"] > 2.0:
                return tall_build
            else:
                return low_build

    if surface_type == "grass":
        return grass_style
    if surface_type == "wild grass":
        return wild_grass_style
    if surface_type == "water":
        # from shapely import affinity
        # return water_style, affinity.rotate(shape, 90, origin='centroid')
        return water_style


if __name__ == "__main__":
    # # Most of Berlin
    # e = ExtentDegrees(
    #     latmin=52.4650,
    #     latmax=52.5805,
    #     lonmin=13.2911,
    #     lonmax=13.5249
    # )

    # # Berlin central station
    # extent = ExtentDegrees(
    #     latmin=52.5275,
    #     latmax=52.5356,
    #     lonmin=13.3613,
    #     lonmax=13.3768,
    # )
    # # small piece of Central Park in NY
    # extent = ExtentDegrees(
    #     latmin=40.78040,
    #     latmax=40.78280,
    #     lonmin=-73.96050,
    #     lonmax=-73.96350,
    # )

    # # Bicocca University main buildings, Milan, Italy
    # extent = ExtentDegrees(
    #     latmin=45.5098,
    #     latmax=45.5200,
    #     lonmin=9.2041,
    #     lonmax=9.2195,
    # )
    # northern part or Rostock, Germany
    extent = ExtentDegrees(
        latmin=54.0960,
        latmax=54.2046,
        lonmin=12.0029,
        lonmax=12.1989,
    )

    # most of Berlin, takes:
    # 6 minutes to read all the data
    # 4 minutes to generate the figure
    # 2 minutes to generate the PNG
    # 2 minutes to generate the SVG
    # 1 minute to generate the geoTIFF
    # extent = ExtentDegrees(
    #     latmin=52.4215,
    #     latmax=52.6106,
    #     lonmin=13.1180,
    #     lonmax=13.6368,
    # )

    loop = asyncio.get_event_loop()
    db_data = loop.run_until_complete(data_from_extent(extent))
    logger.info("Data has been read, processing...")
    reprs = data_to_representation(db_data, entity_callback=nice_representation)
    logger.info("Representation has been calculated, generating figure...")

    db_img = representation_to_figure(reprs, extent, nice_renderer, figsize=3000)
    # db_img = map_to_figure(extent, db_data, way_callback=nice_callback, relation_callback=nice_callback, figsize=2500)
    logger.info("Figure is ready, persisting to PNG...")

    db_img.savefig("piece_generated.png")
    logger.info("Figure is ready, persisting to SVG...")

    db_img.savefig("piece_generated.svg")

    logger.info("Figure is ready, persisting to geoTIFF...")

    rasterized = figure_to_numpy(db_img)
    save_to_geoTIFF(extent, rasterized, "piece_generated.tif")
    logger.info("done!")

    exit()

    import json
    from shapely.geometry import shape
    from geoshiny.draw_helpers import render_shapes_to_figure, figure_to_numpy

    line_geojson = '{"type":"Polygon","coordinates":[[[13.3730741,52.528892399],[13.3732394,52.528739999],[13.3733324,52.528769599],[13.3734522,52.528810199],[13.3736096,52.528858799],[13.3744697,52.529166499],[13.3747036,52.529250199],[13.3748861,52.529311299],[13.3749662,52.529338699],[13.3745283,52.529799099],[13.3742478,52.529694699],[13.374134,52.529808599],[13.3737474,52.529675299],[13.373759,52.529665399],[13.3738839,52.529534099],[13.3736457,52.529450199],[13.3735978,52.529432699],[13.3738416,52.529166699],[13.3730741,52.528892399]],[[13.3733161,52.528932899],[13.3735506,52.529015099],[13.3736102,52.528954699],[13.3733767,52.528872999],[13.3733161,52.528932899]],[[13.3736913,52.529063299],[13.3738527,52.529120799],[13.3739092,52.529059099],[13.3737474,52.529001599],[13.3736913,52.529063299]],[[13.3738146,52.529369699],[13.3738877,52.529395999],[13.373992,52.529289999],[13.3739195,52.529263899],[13.3738146,52.529369699]],[[13.3739585,52.529161699],[13.374125,52.529221599],[13.3741824,52.529159999],[13.3740189,52.529101199],[13.3739585,52.529161699]],[[13.3739754,52.529504299],[13.3742818,52.529615199],[13.3744435,52.529445099],[13.3741371,52.529335599],[13.3739754,52.529504299]],[[13.3742729,52.529277899],[13.3744951,52.529357999],[13.3745516,52.529295799],[13.374334,52.529217499],[13.3742729,52.529277899]],[[13.3744009,52.529653699],[13.3744945,52.529685499],[13.3746104,52.529557999],[13.3745186,52.529527799],[13.3744009,52.529653699]],[[13.374605,52.529450799],[13.3746828,52.529479599],[13.3747424,52.529415999],[13.3746646,52.529386499],[13.374605,52.529450799]]]}'
    multipolygon = shape(json.loads(line_geojson))

    line_geojson2 = '{"type":"Polygon","coordinates":[[[13.370113,52.533598999],[13.3703205,52.533418499],[13.3707833,52.533616299],[13.3709272,52.533677799],[13.3708984,52.533702899],[13.3709142,52.533709099],[13.3708979,52.533723799],[13.3708817,52.533738499],[13.3708656,52.533731399],[13.3708095,52.533780199],[13.3708251,52.533786199],[13.3708121,52.533797699],[13.3707991,52.533809199],[13.3707831,52.533803199],[13.3707214,52.533856899],[13.3701753,52.533625399],[13.370113,52.533598999]],[[13.370314,52.533620999],[13.3703358,52.533630599],[13.3703553,52.533628799],[13.3705487,52.533709399],[13.3705595,52.533735699],[13.3705824,52.533744899],[13.3706001,52.533727299],[13.3705982,52.533722699],[13.3706835,52.533648599],[13.370691,52.533648899],[13.370708,52.533634499],[13.3706765,52.533622099],[13.3706325,52.533628399],[13.3704518,52.533552499],[13.3704478,52.533530099],[13.3704249,52.533521099],[13.370314,52.533620999]]]}'
    multipolygon2 = shape(json.loads(line_geojson2))

    lines_geojson3 = '{"type":"Polygon","coordinates":[[[13.372177,52.528578699],[13.3722708,52.528484999],[13.372197,52.528457599],[13.3723126,52.528342099],[13.372318,52.528336699],[13.372377,52.528358599],[13.3723713,52.528364299],[13.3725852,52.528443499],[13.372711,52.528317799],[13.3726535,52.528296399],[13.3727006,52.528249399],[13.3726909,52.528245799],[13.3727599,52.528176799],[13.372767,52.528179499],[13.373034,52.527912699],[13.3730277,52.527910399],[13.3730982,52.527839999],[13.3732201,52.527885199],[13.3733491,52.527932999],[13.3732799,52.528002099],[13.3732728,52.527999499],[13.3730044,52.528267599],[13.3730124,52.528270599],[13.3729424,52.528340499],[13.3729341,52.528337499],[13.3728883,52.528383299],[13.3728297,52.528361599],[13.3727029,52.528488199],[13.3727133,52.528491999],[13.372505,52.528700199],[13.3723248,52.528633399],[13.3721843,52.528581399],[13.372177,52.528578699]]]}'
    multipolygon3 = shape(json.loads(lines_geojson3))

    # this extent contains the above feature in its North-East corner

    fig = render_shapes_to_figure(
        extent,
        [
            (multipolygon, dict(facecolor="#ff0000", edgecolor="black", alpha=0.5)),
            (multipolygon2, dict(facecolor="#00ff00", edgecolor="blue")),
            (multipolygon3, dict(facecolor="yellow", edgecolor="blue")),
        ],
    )
    fig.savefig("image.png")

    way_callback = any_way_callback

    osm_name = "museum_insel_berlin.osm"
    xml_data, extent = xml_to_map_obj(osm_name)
    xml_img = map_to_image(
        extent, xml_data, way_callback=way_callback, relation_callback=any_rel_callback
    )
    save_to_geoTIFF(extent, xml_img, "image_from_xml.tif")

    db_data = data_from_extent(extent)
    db_img = map_to_image(
        extent, db_data, way_callback=way_callback, relation_callback=any_rel_callback
    )
    save_to_geoTIFF(extent, db_img, "image_from_db.tif")

    # for osm_name in ['new_york_park.osm', 'sample.osm', 'museum_insel_berlin.osm']:
    #     d, e = xml_to_map_obj(osm_name)
    #     img = asphalt_map(d, e)
    #     save_to_geoTIFF(e, img, osm_name + '.asphalt.tif')

    #     d2 = data_from_extent(e)
    #     img2 = asphalt_map(d2, e)
    #     save_to_geoTIFF(e, img2, osm_name + '.db.asphalt.tif')
