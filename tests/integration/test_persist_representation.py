import filecmp

from shapely.geometry.base import BaseGeometry

from tilesgis.types import ExtentDegrees, OSMWay
from tilesgis.database_extract import data_from_extent
from tilesgis.draw_helpers import (
    data_to_representation,
    data_to_representation_file,
    file_to_representation,
    representation_to_figure,
)


def nice_representation(w: OSMWay):
    if w.attributes is None:
        return

    if w.attributes.get('bicycle') == 'designated':
        return dict(path_type='bike')
    if 'water' in w.attributes:
        return dict(surface_type='water')

    if w.attributes.get('landuse') == 'grass':
        return dict(surface_type='grass')
    if w.attributes.get('leisure') == 'park':
        return dict(surface_type='grass')
    if w.attributes.get('natural') == 'scrub':
        return dict(surface_type='wild grass')

    if 'building' in w.attributes and w.attributes['building'] != 'no':
        if 'building:levels' not in w.attributes:
            return dict(surface_type='building')
        else:
            try:
                level_num = float(w.attributes['building:levels'])
            except ValueError:
                return dict(surface_type='building')
            return dict(surface_type='building', floors=level_num)


def nice_renderer(d: dict, shape: BaseGeometry = None):
    water_style = dict(facecolor='blue', edgecolor='darkblue', linewidth=0.1)
    grass_style = dict(facecolor='green', linewidth=0.1)
    wild_grass_style = dict(facecolor='darkgreen', linewidth=0.1)

    missing_levels = dict(facecolor='red', edgecolor='darkred', linewidth=0.05)
    tall_build = dict(facecolor='black', edgecolor='black', linewidth=0.05)
    low_build = dict(facecolor='grey', edgecolor='darkgrey', linewidth=0.05)

    bike_path = dict(linestyle='dashed', color='yellow', linewidth=0.1)

    if d.get('path_type') == 'bike':
        return bike_path

    surface_type = d.get('surface_type')
    if surface_type == 'building':
        if 'floors' not in d:
            return missing_levels
        else:
            if d['floors'] > 2.0:
                return tall_build
            else:
                return low_build

    if surface_type == 'grass':
        return grass_style
    if surface_type == 'wild grass':
        return wild_grass_style
    if surface_type == 'water':
        from shapely import affinity
        return water_style, affinity.rotate(shape, 90, origin='centroid')


def test_persist_and_retrieve(tmpdir):
    extent = ExtentDegrees(
        latmin=52.50319,
        latmax=52.50507,
        lonmin=13.22676,
        lonmax=13.23066,
        )
    data = data_from_extent(extent)
    target_file = tmpdir.join('representation.jsonl')
    target_file2 = tmpdir.join('representation2.jsonl')

    with open(target_file, 'w') as tfh:
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
        file_to_representation(open(target_file, 'r')),
        extent,
        nice_renderer,
        figsize=1000,
    )
    t1 = str(tmpdir.join('image1.png'))
    t2 = str(tmpdir.join('image2.png'))
    t3 = str(tmpdir.join('image3.png'))

    img1.savefig(t1)
    img2.savefig(t2)
    img3.savefig(t3)

    assert filecmp.cmp(t1, t2, shallow=False)
    # reading from a file handler gives the same result
    assert filecmp.cmp(t2, t3, shallow=False)
