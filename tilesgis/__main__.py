from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import logging
from json import JSONEncoder
import random
from typing import Dict, List, Optional, Tuple
from xml.dom.minidom import parse

from osgeo import gdal
from osgeo import osr
import numpy as np
from PIL import Image, ImageDraw


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
)

logger = logging.getLogger(__name__)


@dataclass
class ExtentDegrees:
    """Bounding box in WGS84 degrees."""
    latmin: float
    latmax: float
    lonmin: float
    lonmax: float


@dataclass
class OSMNode:
    """OSM Node object."""
    lat: float
    lon: float
    attributes: Optional[Dict[str, str]] = None


@dataclass
class OSMWay:
    """OSM Way object."""
    nodes: List[int] = field(default_factory=list)
    attributes: Optional[Dict[str, str]] = None


class RelMemberType(Enum):
    NODE = 1
    WAY = 2


@dataclass
class OSMRelation:
    """OSM Relation object."""
    members: List[Tuple[RelMemberType, int, str]] = field(default_factory=list)
    attributes: Optional[Dict[str, str]] = None


@dataclass
class AreaData:
    """Geographical data for some area."""
    nodes: Dict[int, OSMNode] = field(default_factory=dict)
    ways: Dict[int, OSMWay] = field(default_factory=dict)
    relations: Dict[int, OSMRelation] = field(default_factory=dict)


def xml_to_map_obj(fname: str) -> Tuple[AreaData, ExtentDegrees]:
    """Parse an XML from OSM into an area data object."""
    ret = AreaData()
    dom = parse(fname)
    # get the extent
    bnd = dom.getElementsByTagName('bounds')[0]
    extent = ExtentDegrees(
        latmin=float(bnd.getAttribute('minlat')),
        latmax=float(bnd.getAttribute('maxlat')),
        lonmin=float(bnd.getAttribute('minlon')),
        lonmax=float(bnd.getAttribute('maxlon'))
    )
    # extract the nodes
    for n in dom.getElementsByTagName('node'):
        newNode = OSMNode(
            lat=float(n.getAttribute('lat')),
            lon=float(n.getAttribute('lon'))
        )
        for tag in n.childNodes:
            if tag.nodeType == n.ELEMENT_NODE:
                if newNode.attributes is None:
                    newNode.attributes = {}
                newNode.attributes[tag.getAttribute('k')] = tag.getAttribute('v')

        ret.nodes[int(n.getAttribute('id'))] = newNode

    # now the ways
    for w in dom.getElementsByTagName('way'):
        newWay = OSMWay()
        for nd in w.getElementsByTagName('nd'):
            newWay.nodes.append(int(nd.getAttribute('ref')))
        for tag in w.getElementsByTagName('tag'):
            if newWay.attributes is None:
                newWay.attributes = {}
            newWay.attributes[tag.getAttribute('k')] = tag.getAttribute('v')
        ret.ways[int(w.getAttribute('id'))] = newWay

    # finally, the relations
    for rel in dom.getElementsByTagName('relation'):
        newRel = OSMRelation()
        for member in rel.getElementsByTagName('member'):
            newRel.members.append((
                RelMemberType.WAY if member.getAttribute('type') == 'way' else RelMemberType.NODE,
                int(member.getAttribute('ref')),
                member.getAttribute('role')
                ))
        for tag in rel.getElementsByTagName('tag'):
            if newRel.attributes is None:
                newRel.attributes = {}
            newRel.attributes[tag.getAttribute('k')] = tag.getAttribute('v')
        ret.relations[int(rel.getAttribute('id'))] = newRel

    return ret, extent


def save_to_geoTIFF(bbox: ExtentDegrees, image: np.ndarray, fname: str):
    nx, ny = image.shape[:2]
    # this is because the image is distorted if not square
    assert nx == ny
    xres = (bbox.lonmax - bbox.lonmin) / nx
    yres = (bbox.latmax - bbox.latmin) / ny
    geotransform = (bbox.lonmin, xres, 0, bbox.latmax, 0, -yres)

    dst_ds = gdal.GetDriverByName('GTiff').Create(fname, ny, nx, 3, gdal.GDT_Byte)

    srs = osr.SpatialReference()            # establish encoding
    srs.ImportFromEPSG(4326)                # WGS84 lat/long (in degrees)
    dst_ds.SetGeoTransform(geotransform)    # specify coords
    dst_ds.SetProjection(srs.ExportToWkt())  # export coords to the file
    # image uses cartesian coordinates, swap to graphics coordinates
    # which means to invert Y axis
    img = np.flip(image, (0))
    dst_ds.GetRasterBand(1).WriteArray(img[:, :,  0])
    dst_ds.GetRasterBand(2).WriteArray(img[:, :,  1])
    dst_ds.GetRasterBand(3).WriteArray(img[:, :,  2])
    dst_ds.FlushCache()


def coord_to_pixel(lat: float, lon: float, height: float, width: float, extent: ExtentDegrees) -> Tuple[float, float]:
    """Convert lat/lon coordinate to a pixel coordinate for a given area.

    NOTE: this assumes the extent is very small, enough to not introduce errors
    due to curvature. For this project is usually no bigger than a few blocks,
    but a city should be fine too.
    """
    x = (lon - extent.lonmin) * width / (extent.lonmax - extent.lonmin)
    y = (lat - extent.latmin) * height / (extent.latmax - extent.latmin)

    return x, y


def asphalt_map(data: AreaData, extent: ExtentDegrees) -> np.ndarray:
    """Calculate the image with ways within the given extent."""
    img = Image.new('RGB', (800, 800), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    asphalt_ways = []
    for w in data.ways.values():
        if w.attributes is None:
            continue
        if w.attributes.get('surface') == 'asphalt':
            asphalt_ways.append(w.nodes)

    for way in asphalt_ways:
        red = random.randint(1, 250)
        green = random.randint(1, 250)
        blue = random.randint(1, 250)
        for id1, id2 in zip(way, way[1:]):
            n1 = data.nodes.get(id1)
            n2 = data.nodes.get(id2)
            if n1 is None or n2 is None:
                continue
            # now n1 and n2 are two nodes connected by asphalt
            x1, y1 = coord_to_pixel(n1.lat, n1.lon, img.size[0], img.size[1], extent)
            x2, y2 = coord_to_pixel(n2.lat, n2.lon, img.size[0], img.size[1], extent)
            draw.line((x1, y1, x2, y2), fill=(red, green, blue))

    return np.array(img)


class EnhancedJSONEncoder(JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, Enum):
            return o.name
        return super().default(o)


if __name__ == '__main__':
    osm_fname = 'map.osm'
    d, e = xml_to_map_obj(osm_fname)
    img = asphalt_map(d, e)

    save_to_geoTIFF(e, img, osm_fname + '.asphalt.tif')

    # import json
    # with open(osm_fname + '.json', 'w') as fw:
    #     fw.write(json.dumps(d, indent=2, cls=EnhancedJSONEncoder))

    # from random import randint
    # image = np.zeros((10, 30, 3), dtype=np.uint8)
    # for x in range(0, image.shape[0]):
    #     for y in range(0, image.shape[1]):
    #         image[x][y][0] = randint(1, 255)
    #         image[x][y][1] = randint(1, 255)
    #         image[x][y][2] = randint(1, 255)
    # # coordinates for the Bresso airport landing strip, used here as a reference
    # save_to_geoTIFF(ExtentDegrees(45.5331, 45.5465, 9.1986, 9.2056), image, 'newFile.tif')
