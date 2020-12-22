import filecmp
from typing import Union

from shapely.geometry.base import BaseGeometry

from tilesgis.types import ExtentDegrees, OSMWay, OSMRelation, OSMNode
from tilesgis.database_extract import data_from_extent
from tilesgis.draw_helpers import (
    data_to_representation,
    data_to_representation_file,
    file_to_representation,
    representation_to_figure,
)


def universal_representation(e: Union[OSMWay, OSMRelation, OSMNode]):
    if e.attributes is None:
        return dict(val=1)
    else:
        return dict(val=1 + len(e.attributes))


def messy_renderer(d: dict, shape: BaseGeometry = None):
    if shape.type == 'LineString':
        return dict(color='red', alpha=(1.0 / d['val']))
    if shape.type == 'Polygon':
        return dict(color='red', alpha=(1.0 / d['val']))
    raise ValueError(f'Unknown shape type {shape.type}')


def test_persist_and_retrieve(tmpdir):
    extent = ExtentDegrees(
        latmin=52.50319,
        latmax=52.50507,
        lonmin=13.22676,
        lonmax=13.23066,
        )
    data = data_from_extent(extent)
    target_file = tmpdir.join('representation.jsonl')
    with open(target_file, 'w') as tfh:
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
    t1 = str(tmpdir.join('image1.png'))
    t2 = str(tmpdir.join('image2.png'))

    img1.savefig(t1)
    img2.savefig(t2)
    assert filecmp.cmp(t1, t2, shallow=False)
