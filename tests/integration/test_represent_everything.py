import filecmp

import pytest
from shapely.geometry.base import BaseGeometry

from geoshiny.types import ExtentDegrees, Geometry2DStyle
from geoshiny.database_extract import raw_data_from_extent
from geoshiny.draw_helpers import (
    data_to_representation,
    data_to_representation_file,
    file_to_representation,
    representation_to_figure,
)


def universal_representation(osm_id: int, geom, tags: dict):
    return dict(val=1 + len(tags))


def messy_renderer(d: dict, shape: BaseGeometry = None):
    if shape.type == "LineString":
        return Geometry2DStyle(color="red", alpha=(1.0 / d["val"]))
    if shape.type == "Polygon":
        return Geometry2DStyle(color="green", alpha=(1.0 / d["val"]))
    if shape.type == "Point":
        return Geometry2DStyle(color="blue", alpha=(1.0 / d["val"]))
    raise ValueError(f"Unknown shape type {shape.type}")


@pytest.mark.asyncio
async def test_persist_and_retrieve(tmpdir):
    extent = ExtentDegrees(
        latmin=52.5275,
        latmax=52.5356,
        lonmin=13.3613,
        lonmax=13.3768,
    )
    data = await raw_data_from_extent(extent)
    target_file = tmpdir.join("representation.jsonl")
    with open(target_file, "w") as tfh:
        data_to_representation_file(
            data,
            tfh,
            entity_callback=universal_representation,
        )
    reprs = data_to_representation(
        data,
        entity_callback=universal_representation,
    )
    img1 = representation_to_figure(
        reprs,
        extent,
        messy_renderer,
        figsize=1000,
    )
    img2 = representation_to_figure(
        file_to_representation(str(target_file)),
        extent,
        messy_renderer,
        figsize=1000,
    )
    t1 = str(tmpdir.join("image1.png"))
    t2 = str(tmpdir.join("image2.png"))

    img1.savefig(t1)
    img2.savefig(t2)
    assert filecmp.cmp(t1, t2, shallow=False)
