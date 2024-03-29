from dataclasses import dataclass, fields
from typing import Optional

from pyproj import Transformer
from shapely.geometry.base import BaseGeometry


TRAN_4326_TO_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857")


@dataclass
class Geometry2DStyle:
    """Style for any geometry in a 2D chart."""

    facecolor: Optional[str] = None
    edgecolor: Optional[str] = None
    linewidth: Optional[float] = None
    linestyle: Optional[str] = None
    color: Optional[str] = None
    alpha: Optional[float] = None
    shape: Optional[BaseGeometry] = None
    label: Optional[dict] = None
    # if not None, how much area on the toal must a shape have to be drawn
    min_label_area_ratio: Optional[float] = None

    def get_drawing_options(self):
        """Get the option to draw this element."""
        ret = {}
        for field in fields(self):
            if field.name in ("shape", "label", "min_label_area_ratio"):
                continue
            value = getattr(self, field.name)
            if value is not None:
                ret[field.name] = value
        return ret

    def get_label_options(self):
        if self.label is None:
            return None
        return self.label


@dataclass
class ExtentDegrees:
    """Bounding box in WGS84 degrees. Aka EPSG:4326"""

    latmin: float
    latmax: float
    lonmin: float
    lonmax: float

    def enlarged(self, factor: float):
        """Calculate an extent enlarged in all directions.

        The factor is RELATIVE, 0 means no change, 1.0 means 100% larger,
        -0.5 means 50% smaller

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
        """Convert the extent to a tuple in EPSG 3857.

        The order is the same required by PostGIS st_makeenvelope
        that is: lonmin, latmin, lonmax, latmax
        """
        lonmin, latmin = TRAN_4326_TO_3857.transform(self.latmin, self.lonmin)
        lonmax, latmax = TRAN_4326_TO_3857.transform(self.latmax, self.lonmax)
        return (lonmin, latmin, lonmax, latmax)


@dataclass
class GeomRepresentation:
    properties: dict
    geometry: Optional[BaseGeometry] = None
