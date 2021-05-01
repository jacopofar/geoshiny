## Geoshiny

This is a tool to create customized maps using OpenStreetMap data.

__NOTE__: this software is under development, the interface and the functionalities can and probably will change.

## Features

* Generate customized maps of cities and small regions
* Outputs:
  * geo-referenced TIFF (GeoTIFF)
  * SVG
  * PNG
  * many others
* Store a filtered intermediate representation in JSONL to easily generate images without a database

## Input data

First you need a PostGIS database with the data to represent in flex format. To create that, get a PDB file of the region you are interested to represent (you can also import the whole planet.osm file) and use osm2pgsql with the flex output to run the [pgosm-flex](https://github.com/rustprooflabs/pgosm-flex) scripts.

If you have Docker, you can find a script that populates a PostGIS instance for you in `script_utils/database_from_pbf.sh`, run it with the pbf file name as an argument.

The connection string for this database has to be put in the environment variable `PGIS_CONN_STR`

    export PGIS_CONN_STR=postgres://username:password@localhost:5432/osm_data


## Usage

The library expects two callbacks.

One is the `representation`, which is called for each map feature in the given extent, it receives the OSM tags as an input and returns `None` for features to be ignored or an arbitrary Python object (usually a dictionary) with the relevant information to represent. Can also alter the Shapely geometry.

The other is `renderer`, and it will receive the output of the `representation` function and produce the matplotlib attributes like color and alpha.

The representation can be stored in JSONL with the geoJSON data using `file_to_representation`, doing so you can generateb the representation once and render different extents with different styles easily without even running a database instance.

```python
import asyncio

from geoshiny.database_extract import data_from_extent
from geoshiny.types import (
    ExtentDegrees,
    ObjectStyle,
)

from geoshiny.draw_helpers import (
    data_to_representation,
    data_to_representation_file,
    file_to_representation,
    representation_to_figure,
)

def representation(osm_id: int, geom, tags: dict) -> Optional[dict]:
    if tags.get("bicycle") == "designated":
        return dict(path_type="bike")
    if "water" in tags:
        return dict(surface_type="water")

    if tags.get("landuse") == "grass":
        return dict(surface_type="grass")
    if tags.get("leisure") == "park":
        return dict(surface_type="grass")
    [...]

def renderer(osm_id: int, shape: BaseGeometry, d: dict):
    water_style = ObjectStyle(facecolor="blue", edgecolor="darkblue", linewidth=0.1)
    grass_style = ObjectStyle(facecolor="green", linewidth=0.1)

    if d.get("surface_type") == "water":
        return water_style
    [...]

# northern part of Rostock, Germany
extent = ExtentDegrees(
        latmin=54.0960,
        latmax=54.2046,
        lonmin=12.0029,
        lonmax=12.1989,
    )
loop = asyncio.get_event_loop()
db_data = loop.run_until_complete(data_from_extent(extent))
reprs = data_to_representation(db_data, entity_callback=representation)

db_img = representation_to_figure(reprs, extent, renderer, figsize=3000)

db_img.savefig("image.png")
db_img.savefig("image.svg")

data_to_representation_file(
        db_data,
        'somefile.jsonl',
        entity_callback=representation,
    )
img2 = representation_to_figure(
        file_to_representation('somefile.jsonl'),
        extent,
        renderer,
        figsize=3000,
    )
img2.savefig("image2.png")

```

# TODO

- [ ] Proper automated tests with a reasonable data fixture
- [ ] Add labeling/text
- [ ] XKCD style output (from matplotlib, should work out of the box)
- [ ] Offer both async and sync access if possible, hiding the loop to sync users
- [ ] Visual comparison of output images (may require opencv as a test dependency, is it worth it?)
- [ ] Helper to generate world files (https://en.wikipedia.org/wiki/World_file)
- [ ] 3D output (check QGIS formats / glTF)
- [ ] tileset output?
- [ ] Create and document helpers to make the usage simpler (once the interface is stabilized)
- [ ] Exmaples and screenshot gallery
- [ ] Spatialite support?
- [ ] Optional pipeline definition interface to combine processing steps?
- [ ] Graph functionalities (e.g. show road distance from a set of POI) ?
- [ ] MoviePy integration example
- [ ] Integrated webserver/UI? Maybe better off as a separate thing
