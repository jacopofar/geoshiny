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

from geoshiny import generate_chart

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
    generate_chart('generated.png', extent, nice_representation, nice_renderer)
    logger.info("done!")
