import pytest

from geocrazy.types import ExtentDegrees
from geocrazy.database_extract import data_from_extent


@pytest.mark.asyncio
async def test_complete_retrieval():
    extent = ExtentDegrees(
        latmin=54.0960,
        latmax=54.2046,
        lonmin=12.0029,
        lonmax=12.1989,
    )
    data = await data_from_extent(extent)
    # TODO once a data fixture is stable, put a precise number here
    assert len(data) > 1000
