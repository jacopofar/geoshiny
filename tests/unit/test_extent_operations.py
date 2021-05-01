from geoshiny.types import ExtentDegrees


def test_extent_operations():
    extent = ExtentDegrees(
        latmin=52.51302, latmax=52.51605, lonmin=13.40875, lonmax=13.41547
    )
    assert extent.enlarged(0.1).as_e7_dict() == {
        "latmin": 525128684,
        "latmax": 525162014,
        "lonmin": 134084139,
        "lonmax": 134158059,
    }

    # negative longitude (New York)
    extent = ExtentDegrees(
        latmin=40.78793, latmax=40.79170, lonmin=-73.96017, lonmax=-73.95175
    )
    assert extent.enlarged(0.1).as_e7_dict() == {
        "latmin": 407877415,
        "latmax": 407918885,
        "lonmin": -739605910,
        "lonmax": -739513290,
    }
