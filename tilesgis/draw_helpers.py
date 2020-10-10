import logging
from typing import Tuple

from PIL import Image, ImageDraw
from matplotlib import pyplot
import numpy as np

from tilesgis.types import ExtentDegrees, AreaData

logger = logging.getLogger(__name__)


def coord_to_pixel(lat: float, lon: float, height: float, width: float, extent: ExtentDegrees) -> Tuple[float, float]:
    """Convert lat/lon coordinate to a pixel coordinate for a given area.

    NOTE: this assumes the extent is very small, enough to not introduce errors
    due to curvature. For this project is usually no bigger than a few blocks,
    but a city should be fine too.
    """
    x = (lon - extent.lonmin) * width / (extent.lonmax - extent.lonmin)
    y = (lat - extent.latmin) * height / (extent.latmax - extent.latmin)

    return x, y


def map_to_image(
    extent: ExtentDegrees,
    data: AreaData,
    point_callback=None,
    way_callback=None,
    relation_callback=None,
        ):
    img = Image.new('RGB', (800, 800), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    ways_to_draw = []

    if way_callback is not None:
        for w in data.ways.values():
            color = way_callback(w)
            if color is not None:
                ways_to_draw.append((w.nodes, color))

    for way, color in ways_to_draw:
        for id1, id2 in zip(way, way[1:]):
            n1 = data.nodes.get(id1)
            n2 = data.nodes.get(id2)
            if n1 is None or n2 is None:
                continue
            # now n1 and n2 are two nodes connected in a way
            x1, y1 = coord_to_pixel(n1.lat, n1.lon, img.size[0], img.size[1], extent)
            x2, y2 = coord_to_pixel(n2.lat, n2.lon, img.size[0], img.size[1], extent)
            draw.line((x1, y1, x2, y2), fill=color)  # type: ignore

    pyplot.show()
    return np.array(img)
