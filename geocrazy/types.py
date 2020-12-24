from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pyproj import Transformer


TRAN_4326_TO_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857")


@dataclass
class ExtentDegrees:
    """Bounding box in WGS84 degrees. Aka EPSG:4326"""
    latmin: float
    latmax: float
    lonmin: float
    lonmax: float

    def enlarged(self, factor: float):
        """Calculate an extent enlarged in all directions.

        Parameters
        ----------
        factor : float
            How much to enlarge, e.g. 0.1 means 10% more
        """
        lat_mid = (self.latmax + self.latmin) / 2
        lat_radius = abs(self.latmax - self.latmin) / 2 * (1 + factor)
        lon_mid = (self.lonmax + self.lonmin) / 2
        lon_radius = abs(self.lonmax - self.lonmin) / 2 * (1 + factor)
        return ExtentDegrees(
            latmin=min(lat_mid - lat_radius, lat_mid + lat_radius),
            latmax=max(lat_mid - lat_radius, lat_mid + lat_radius),
            lonmin=min(lon_mid - lon_radius, lon_mid + lon_radius),
            lonmax=max(lon_mid - lon_radius, lon_mid + lon_radius),
        )

    def as_e7_dict(self):
        return dict(
            latmin=int(self.latmin * 10 ** 7),
            latmax=int(self.latmax * 10 ** 7),
            lonmin=int(self.lonmin * 10 ** 7),
            lonmax=int(self.lonmax * 10 ** 7),
        )

    def as_epsg3857(self):
        lonmin, latmin = TRAN_4326_TO_3857.transform(self.latmin, self.lonmin)
        lonmax, latmax = TRAN_4326_TO_3857.transform(self.latmax, self.lonmax)
        return dict(
            latmin=latmin,
            latmax=latmax,
            lonmin=lonmin,
            lonmax=lonmax,
        )


@dataclass
class OSMNode:
    """OSM Node object."""
    lat: float
    lon: float
    attributes: Optional[Dict[str, str]] = None
    geoJSON: Optional[str] = None


@dataclass
class OSMWay:
    """OSM Way object."""
    nodes: List[int] = field(default_factory=list)
    attributes: Optional[Dict[str, str]] = None
    geoJSON: Optional[str] = None


class RelMemberType(Enum):
    NODE = 1
    WAY = 2


@dataclass
class OSMRelation:
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