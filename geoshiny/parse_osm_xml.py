from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Dict, List, Optional, Tuple
from xml.dom.minidom import parse

from geoshiny.types import ExtentDegrees


@dataclass
class OSMEntity:
    """General entity expected by the render callback.
    This is not supposed to be created directly, is just a simple way to
    have the equivalent of an interface in Python without messy ABCs
    """

    geoJSON: Optional[str] = None


@dataclass
class OSMNode(OSMEntity):
    """OSM Node object."""

    lat: Optional[float] = None
    lon: Optional[float] = None
    attributes: Optional[Dict[str, str]] = None
    geoJSON: Optional[str] = None


@dataclass
class OSMWay(OSMEntity):
    """OSM Way object."""

    nodes: List[int] = field(default_factory=list)
    attributes: Optional[Dict[str, str]] = None
    geoJSON: Optional[str] = None


class RelMemberType(Enum):
    NODE = 1
    WAY = 2


@dataclass
class OSMRelation(OSMEntity):
    """OSM Relation object."""

    members: List[Tuple[RelMemberType, int, str]] = field(default_factory=list)
    attributes: Optional[Dict[str, str]] = None
    geoJSON: Optional[str] = None


@dataclass
class AreaData:
    """OSM data for some area."""

    nodes: Dict[int, OSMNode] = field(default_factory=dict)
    ways: Dict[int, OSMWay] = field(default_factory=dict)
    relations: Dict[int, OSMRelation] = field(default_factory=dict)


def xml_to_map_obj(fname: str) -> Tuple[AreaData, ExtentDegrees]:
    """Parse an XML from OSM into an area data object."""
    ret = AreaData()
    dom = parse(fname)
    # get the extent
    bnd = dom.getElementsByTagName("bounds")[0]
    extent = ExtentDegrees(
        latmin=float(bnd.getAttribute("minlat")),
        latmax=float(bnd.getAttribute("maxlat")),
        lonmin=float(bnd.getAttribute("minlon")),
        lonmax=float(bnd.getAttribute("maxlon")),
    )
    # extract the nodes
    for n in dom.getElementsByTagName("node"):
        newNode = OSMNode(
            lat=float(n.getAttribute("lat")), lon=float(n.getAttribute("lon"))
        )
        for tag in n.childNodes:
            if tag.nodeType == n.ELEMENT_NODE:
                if newNode.attributes is None:
                    newNode.attributes = {}
                newNode.attributes[tag.getAttribute("k")] = tag.getAttribute("v")

        ret.nodes[int(n.getAttribute("id"))] = newNode

    # now the ways
    for w in dom.getElementsByTagName("way"):
        newWay = OSMWay()
        for nd in w.getElementsByTagName("nd"):
            newWay.nodes.append(int(nd.getAttribute("ref")))
        for tag in w.getElementsByTagName("tag"):
            if newWay.attributes is None:
                newWay.attributes = {}
            newWay.attributes[tag.getAttribute("k")] = tag.getAttribute("v")
        ret.ways[int(w.getAttribute("id"))] = newWay

    # finally, the relations
    for rel in dom.getElementsByTagName("relation"):
        newRel = OSMRelation()
        for member in rel.getElementsByTagName("member"):
            newRel.members.append(
                (
                    RelMemberType.WAY
                    if member.getAttribute("type") == "way"
                    else RelMemberType.NODE,
                    int(member.getAttribute("ref")),
                    member.getAttribute("role"),
                )
            )
        for tag in rel.getElementsByTagName("tag"):
            if newRel.attributes is None:
                newRel.attributes = {}
            newRel.attributes[tag.getAttribute("k")] = tag.getAttribute("v")
        ret.relations[int(rel.getAttribute("id"))] = newRel

    return ret, extent
