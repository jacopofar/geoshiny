import filecmp

import pytest
from shapely.geometry.base import BaseGeometry
from shapely import affinity

from geoshiny.types import ExtentDegrees, ObjectStyle
from geoshiny.database_extract import raw_data_from_extent
from geoshiny.draw_helpers import (
    data_to_representation,
    data_to_representation_file,
    file_to_representation,
    representation_to_figure,
)


def nice_representation(osm_id: int, geom, tags: dict):
    if tags is None:
        return

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
                return dict(surface_type="building")
            return dict(surface_type="building", floors=level_num)


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
        water_style.shape = affinity.rotate(shape, 90, origin="centroid")
        return water_style

# fail because of https://github.com/Toblerity/Shapely/issues/1100
@pytest.mark.xfail
@pytest.mark.asyncio
async def test_persist_and_retrieve(tmpdir):
    # northern part of Rostock, Germany
    extent = ExtentDegrees(
        latmin=54.0960,
        latmax=54.2046,
        lonmin=12.0029,
        lonmax=12.1989,
    )
    data = await raw_data_from_extent(extent)
    target_file = tmpdir.join("representation.jsonl")
    target_file2 = tmpdir.join("representation2.jsonl")

    with open(target_file, "w") as tfh:
        data_to_representation_file(
            data,
            tfh,
            entity_callback=nice_representation,
        )
    data_to_representation_file(
        data,
        str(target_file2),
        entity_callback=nice_representation,
    )
    # ensure passing an handler and a file name brings the same result
    assert filecmp.cmp(str(target_file), str(target_file2), shallow=False)

    reprs = data_to_representation(
        data,
        entity_callback=nice_representation,
    )
    img1 = representation_to_figure(
        reprs,
        extent,
        nice_renderer,
        figsize=1000,
    )
    img2 = representation_to_figure(
        file_to_representation(str(target_file)),
        extent,
        nice_renderer,
        figsize=1000,
    )
    img3 = representation_to_figure(
        file_to_representation(open(target_file, "r")),
        extent,
        nice_renderer,
        figsize=1000,
    )
    t1 = str(tmpdir.join("image1.png"))
    t2 = str(tmpdir.join("image2.png"))
    t3 = str(tmpdir.join("image3.png"))

    img1.savefig(t1)
    img2.savefig(t2)
    img3.savefig(t3)

    assert filecmp.cmp(t1, t2, shallow=False)
    # reading from a file handler gives the same result
    assert filecmp.cmp(t2, t3, shallow=False)
