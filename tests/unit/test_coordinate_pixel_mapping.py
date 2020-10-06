from pytest import approx

from tilesgis.__main__ import coord_to_pixel, ExtentDegrees


def test_coord_to_pixel():
    extent = ExtentDegrees(
        latmin=52.51302,
        latmax=52.51605,
        lonmin=13.40875,
        lonmax=13.41547)
    assert coord_to_pixel(extent.latmax, extent.lonmax, 100, 100, extent) == (100.0, 100.0)
    assert coord_to_pixel(extent.latmin, extent.lonmin, 100, 100, extent) == (0.0, 0.0)
    # negative longitude (New York)
    extent = ExtentDegrees(
        latmin=40.78793,
        latmax=40.79170,
        lonmin=-73.96017,
        lonmax=-73.95175)
    assert coord_to_pixel(extent.latmax, extent.lonmax, 100, 100, extent) == (100.0, 100.0)
    assert coord_to_pixel(extent.latmin, extent.lonmin, 100, 100, extent) == (0.0, 0.0)
    assert coord_to_pixel(
        (extent.latmax + extent.latmin) / 2.0,
        (extent.lonmax + extent.lonmin) / 2.0,
        100, 100, extent) == (approx(50.0, 0.01), approx(50.0, 0.01))

