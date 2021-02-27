import json
import subprocess


def test_aaaaa_weird_anomaly():
    """Okay, this is weird.

    You may be wondering why is there such a test with such a weird name.
    Here I'll try to explain this madness.

    tl;dr:  you have to install Shapely with the --no-binary option, to compile
            it and ensure it has the same GEOS version as GDAL.

            This problem seems specific of macOS

    Now a more detailed explanation:
    GDAL is the library used in this project to generate geoTIFF.
    I don't love it because the docs are a bit weird, but it works.
    OK, it works as long as you don't change the numpy version too much
    and the gotchas are weird (https://gdal.org/api/python_gotchas.html)
    Still, it works so thank you GDAL developers.

    Meanwhile, the project uses Shapely for everything related to GeoJSON
    parsing and processing shapes, and it also uses GEOS.

    As hinted by Shapely README (https://github.com/Toblerity/Shapely/blob/master/README.rst)
    it's a good idea to compile it instead of using the provided wheels.
    I didn't read it and as a result had an interesting adventure.
    Turns out, if you have mismatching versions of GEOS used by Shapely and
    GDAL weird things will happen, for example the valid GeoJSON below gives
    a Null geometry because 'Hole is not a LinearRing'.

    The provided install script should do things correctly, but who knows
    whether people will use it as is or some future release will have similar
    issues? The issue is not evident, the libraries seem to work and give
    runtime errors, also the problem arises only when you import things in a
    precise order.

    After some attempts I came out with this test, the smaller I could produce.

    The name is deliberate to run it as the first test of all and ensure no
    one else imported the libraries, or it may not work.

    Then it imports osgeo to trigger this exact problem.

    SEE ALSO:
    https://github.com/Toblerity/Shapely/issues/416
    """
    import osgeo  # NOQA
    from shapely.geometry import shape

    line_geojson = '{"type":"Polygon","coordinates":[[[13.3730741,52.528892399],[13.3732394,52.528739999],[13.3733324,52.528769599],[13.3734522,52.528810199],[13.3736096,52.528858799],[13.3744697,52.529166499],[13.3747036,52.529250199],[13.3748861,52.529311299],[13.3749662,52.529338699],[13.3745283,52.529799099],[13.3742478,52.529694699],[13.374134,52.529808599],[13.3737474,52.529675299],[13.373759,52.529665399],[13.3738839,52.529534099],[13.3736457,52.529450199],[13.3735978,52.529432699],[13.3738416,52.529166699],[13.3730741,52.528892399]],[[13.3733161,52.528932899],[13.3735506,52.529015099],[13.3736102,52.528954699],[13.3733767,52.528872999],[13.3733161,52.528932899]],[[13.3736913,52.529063299],[13.3738527,52.529120799],[13.3739092,52.529059099],[13.3737474,52.529001599],[13.3736913,52.529063299]],[[13.3738146,52.529369699],[13.3738877,52.529395999],[13.373992,52.529289999],[13.3739195,52.529263899],[13.3738146,52.529369699]],[[13.3739585,52.529161699],[13.374125,52.529221599],[13.3741824,52.529159999],[13.3740189,52.529101199],[13.3739585,52.529161699]],[[13.3739754,52.529504299],[13.3742818,52.529615199],[13.3744435,52.529445099],[13.3741371,52.529335599],[13.3739754,52.529504299]],[[13.3742729,52.529277899],[13.3744951,52.529357999],[13.3745516,52.529295799],[13.374334,52.529217499],[13.3742729,52.529277899]],[[13.3744009,52.529653699],[13.3744945,52.529685499],[13.3746104,52.529557999],[13.3745186,52.529527799],[13.3744009,52.529653699]],[[13.374605,52.529450799],[13.3746828,52.529479599],[13.3747424,52.529415999],[13.3746646,52.529386499],[13.374605,52.529450799]]]}'
    multipolygon = shape(json.loads(line_geojson))

    # it the setup is broken, it raises ValueError: Null geometry has no type
    # and logs the error 'shapely.geos:geos.py:252 Hole is not a LinearRing'
    assert multipolygon.type == "Polygon"

    # NOTE: a few months after writing this test the order broke
    # ON THE OTHER WAY AROUND. Since I can import only in one order and the
    # effect is global, this makes things harder
    # so here I use this abomination to have a clean interpreter
    # to run
    proc = subprocess.Popen(
        "python3 -c 'from shapely.geometry import shape;import osgeo'",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True,
    )
    std_out, std_err = proc.communicate()
    # if there's an error, the trick works
    if "ModuleNotFoundError: No module named '_gdal'" in std_err:
        proc = subprocess.Popen(
            """python3 -c 'from geocrazy import import_hell;import_hell.import_gdal_shapely(wait=False);from shapely.geometry import shape;import osgeo; print("import workaround successful")'""",  # NOQA
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            universal_newlines=True,
        )
        std_out, std_err = proc.communicate()

        assert "import workaround successful" in std_out
