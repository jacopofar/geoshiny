import asyncio
from typing import Callable, List, Optional

from shapely.geometry.base import BaseGeometry

from geoshiny.types import (
    ExtentDegrees,
    ObjectStyle,
)
from geoshiny.database_extract import representation_from_extent
from geoshiny.draw_helpers import (
    data_to_representation,
    representation_to_figure,
)


def generate_chart(
    filename: str,
    extent: ExtentDegrees,
    representer: Callable[[int, BaseGeometry, dict], Optional[dict]],
    renderer: Callable[[int, BaseGeometry, dict], Optional[ObjectStyle]],
    dsn=None,
    figsize=2000,
    tables: Optional[List[str]] = None
):
    loop = asyncio.get_event_loop()
    reprs = loop.run_until_complete(representation_from_extent(extent, representer, dsn=dsn))
    db_img = representation_to_figure(reprs, extent, renderer, figsize=figsize)
    db_img.savefig(filename)
