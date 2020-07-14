from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import logging
from json import JSONEncoder
from typing import Dict, List, Tuple
from xml.dom.minidom import parse

from osgeo import gdal
from osgeo import osr
import numpy as np

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
)

logger = logging.getLogger(__name__)


@dataclass
class ExtendDegrees:
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
    attributes: Dict[str, str] = None


@dataclass
class OSMWay:
    """OSM Way object."""
    nodes: List[int] = field(default_factory=list)
    attributes: Dict[str, str] = None


class RelMemberType(Enum):
    NODE = 1
    WAY = 2


@dataclass
class OSMRelation:
    """OSM Relation object."""
    members: List[Tuple[RelMemberType, int, str]] = field(default_factory=list)
    attributes: Dict[str, str] = None


@dataclass
class AreaData:
    """Geographical data for some area."""
    nodes: Dict[int, OSMNode] = field(default_factory=dict)
    ways: Dict[int, OSMWay] = field(default_factory=dict)
    relations: Dict[int, OSMRelation] = field(default_factory=dict)


def xmlToMapObj(fname: str) -> AreaData:
    """Parse an XML from OSM into an area data object."""
    ret = AreaData()
    dom = parse(fname)
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
        for tag in n.getElementsByTagName('tag'):
            if newWay.attributes is None:
                newWay.attributes = {}
            newWay.attributes[tag.getAttribute('k')] = tag.getAttribute('v')
        ret.ways[int(n.getAttribute('id'))] = newWay

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
        ret.relations[int(n.getAttribute('id'))] = newRel
    return ret


def saveToGeoTIFF(bbox: ExtendDegrees, image: np.ndarray, fname: str):
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
    dst_ds.GetRasterBand(1).WriteArray(image[:, :, 0])   # write r-band to the raster
    dst_ds.GetRasterBand(2).WriteArray(image[:, :, 1])   # write g-band to the raster
    dst_ds.GetRasterBand(3).WriteArray(image[:, :, 2])   # write b-band to the raster
    dst_ds.FlushCache()


class EnhancedJSONEncoder(JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, Enum):
            return o.name
        return super().default(o)


if __name__ == '__main__':
    d = xmlToMapObj('milano_bicocca.osm')
    import json
    with open('bicocca.json', 'w') as fw:
        fw.write(json.dumps(d, indent=2, cls=EnhancedJSONEncoder))
    exit(2)

    from random import randint
    image = np.zeros((10, 30, 3), dtype=np.uint8)
    for x in range(0, image.shape[0]):
        for y in range(0, image.shape[1]):
            image[x][y][0] = randint(1, 255)
            image[x][y][1] = randint(1, 255)
            image[x][y][2] = randint(1, 255)
    # coordinates for the Bresso airport landing strip, used here as a reference
    saveToGeoTIFF(ExtendDegrees(45.5331, 45.5465, 9.1986, 9.2056), image, 'newFile.tif')
