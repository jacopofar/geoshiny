from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


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
    """OSM data for some area."""
    nodes: Dict[int, OSMNode] = field(default_factory=dict)
    ways: Dict[int, OSMWay] = field(default_factory=dict)
    relations: Dict[int, OSMRelation] = field(default_factory=dict)
