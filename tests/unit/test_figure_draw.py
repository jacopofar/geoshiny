import json

from shapely.geometry import shape

from tilesgis.types import ExtentDegrees
from tilesgis.draw_helpers import render_shapes_to_figure

# Geometry types
#  'Point',
#     'LineString',
#     'LinearRing',
#     'Polygon',
#     'MultiPoint',
#     'MultiLineString',
#     'MultiPolygon',
#     'GeometryCollection'


def test_render_polygon(tmpdir):
    # this is a building with many yards, see https://www.openstreetmap.org/relation/56880
    line_geojson = '{"type":"Polygon","coordinates":[[[13.3730741,52.528892399],[13.3732394,52.528739999],[13.3733324,52.528769599],[13.3734522,52.528810199],[13.3736096,52.528858799],[13.3744697,52.529166499],[13.3747036,52.529250199],[13.3748861,52.529311299],[13.3749662,52.529338699],[13.3745283,52.529799099],[13.3742478,52.529694699],[13.374134,52.529808599],[13.3737474,52.529675299],[13.373759,52.529665399],[13.3738839,52.529534099],[13.3736457,52.529450199],[13.3735978,52.529432699],[13.3738416,52.529166699],[13.3730741,52.528892399]],[[13.3733161,52.528932899],[13.3735506,52.529015099],[13.3736102,52.528954699],[13.3733767,52.528872999],[13.3733161,52.528932899]],[[13.3736913,52.529063299],[13.3738527,52.529120799],[13.3739092,52.529059099],[13.3737474,52.529001599],[13.3736913,52.529063299]],[[13.3738146,52.529369699],[13.3738877,52.529395999],[13.373992,52.529289999],[13.3739195,52.529263899],[13.3738146,52.529369699]],[[13.3739585,52.529161699],[13.374125,52.529221599],[13.3741824,52.529159999],[13.3740189,52.529101199],[13.3739585,52.529161699]],[[13.3739754,52.529504299],[13.3742818,52.529615199],[13.3744435,52.529445099],[13.3741371,52.529335599],[13.3739754,52.529504299]],[[13.3742729,52.529277899],[13.3744951,52.529357999],[13.3745516,52.529295799],[13.374334,52.529217499],[13.3742729,52.529277899]],[[13.3744009,52.529653699],[13.3744945,52.529685499],[13.3746104,52.529557999],[13.3745186,52.529527799],[13.3744009,52.529653699]],[[13.374605,52.529450799],[13.3746828,52.529479599],[13.3747424,52.529415999],[13.3746646,52.529386499],[13.374605,52.529450799]]]}'
    multipolygon = shape(json.loads(line_geojson))

    line_geojson2 = '{"type":"Polygon","coordinates":[[[13.370113,52.533598999],[13.3703205,52.533418499],[13.3707833,52.533616299],[13.3709272,52.533677799],[13.3708984,52.533702899],[13.3709142,52.533709099],[13.3708979,52.533723799],[13.3708817,52.533738499],[13.3708656,52.533731399],[13.3708095,52.533780199],[13.3708251,52.533786199],[13.3708121,52.533797699],[13.3707991,52.533809199],[13.3707831,52.533803199],[13.3707214,52.533856899],[13.3701753,52.533625399],[13.370113,52.533598999]],[[13.370314,52.533620999],[13.3703358,52.533630599],[13.3703553,52.533628799],[13.3705487,52.533709399],[13.3705595,52.533735699],[13.3705824,52.533744899],[13.3706001,52.533727299],[13.3705982,52.533722699],[13.3706835,52.533648599],[13.370691,52.533648899],[13.370708,52.533634499],[13.3706765,52.533622099],[13.3706325,52.533628399],[13.3704518,52.533552499],[13.3704478,52.533530099],[13.3704249,52.533521099],[13.370314,52.533620999]]]}'
    multipolygon2 = shape(json.loads(line_geojson2))

    lines_geojson3 = '{"type":"Polygon","coordinates":[[[13.372177,52.528578699],[13.3722708,52.528484999],[13.372197,52.528457599],[13.3723126,52.528342099],[13.372318,52.528336699],[13.372377,52.528358599],[13.3723713,52.528364299],[13.3725852,52.528443499],[13.372711,52.528317799],[13.3726535,52.528296399],[13.3727006,52.528249399],[13.3726909,52.528245799],[13.3727599,52.528176799],[13.372767,52.528179499],[13.373034,52.527912699],[13.3730277,52.527910399],[13.3730982,52.527839999],[13.3732201,52.527885199],[13.3733491,52.527932999],[13.3732799,52.528002099],[13.3732728,52.527999499],[13.3730044,52.528267599],[13.3730124,52.528270599],[13.3729424,52.528340499],[13.3729341,52.528337499],[13.3728883,52.528383299],[13.3728297,52.528361599],[13.3727029,52.528488199],[13.3727133,52.528491999],[13.372505,52.528700199],[13.3723248,52.528633399],[13.3721843,52.528581399],[13.372177,52.528578699]]]}'
    multipolygon3 = shape(json.loads(lines_geojson3))

    # this extent contains the above feature in its North-East corner
    extent = ExtentDegrees(
        latmin=52.5275,
        latmax=52.5356,
        lonmin=13.3613,
        lonmax=13.3768,
    )
    fig = render_shapes_to_figure(
        extent, [
            (multipolygon, dict(
                line=dict(color='#ff0000'),
                vertex=dict(color='#00ff00'),
                vertex_fmt='o',
                )),
            (multipolygon2, dict(
                line=dict(color='#00ff00'),
                vertex=dict(color='#a0ffa0'),
                vertex_fmt='o',
                )),
            (multipolygon3, dict(
                line=dict(color='#00ff00'),
                vertex=dict(color='#a0ffa0'),
                vertex_fmt='o',
                ))
            ])
    for target in ['img.png', 'img.svg']:
        target_file = tmpdir.join(target)
        fig.savefig(str(target_file))
        assert target_file.size() > 5_000



    import numpy as np

    from matplotlib.backends.backend_agg import FigureCanvasAgg

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    buf = canvas.buffer_rgba()
    # convert to a NumPy array
    image_from_plot = np.asarray(buf)
    from tilesgis.__main__ import save_to_geoTIFF
    save_to_geoTIFF(extent, image_from_plot, 'magic_spree.tif')

    assert list(fig.get_size_inches()) == [5.0, 5.0]


def blabla_test_render_line():
    # TODO parse a line GeoJSON and generate a figure from it
    # then also check that it's possible to generate a numpy image from the Figure
    # and an SVG

    # this is a piece of the Spree river, https://www.openstreetmap.org/way/159534658
    line_geojson = '{"type":"LineString","coordinates":[[13.4078083,52.515006699],[13.4070379,52.515127199],[13.4062402,52.515462899],[13.4056683,52.515804299],[13.4051136,52.516166199],[13.4043756,52.516775399],[13.4040558,52.517071899],[13.4026181,52.518489099],[13.402347,52.518765299],[13.4018846,52.519206299],[13.4014628,52.519658399],[13.4009832,52.520096599],[13.4004115,52.520529899],[13.4002128,52.520705699],[13.3999649,52.520930299],[13.3996217,52.521141099],[13.3990601,52.521381799],[13.3980572,52.521627699],[13.3974686,52.521757799],[13.3967584,52.521922799],[13.3956494,52.522172099],[13.3943258,52.522294899],[13.3940589,52.522308699],[13.3929723,52.522386099],[13.3916795,52.522482899],[13.3911731,52.522456499],[13.3894839,52.522337699],[13.3891755,52.522310899],[13.3883252,52.522207199],[13.3879702,52.522111199],[13.3869355,52.521506999],[13.3859434,52.520953799],[13.3854117,52.520654199],[13.3850207,52.520431499],[13.3844628,52.520183399],[13.3836045,52.519903499],[13.3822098,52.519491299],[13.380815,52.519217099],[13.3802539,52.519198999],[13.3795705,52.519177999],[13.3791705,52.519210699],[13.3788613,52.519235899],[13.3785521,52.519290699],[13.3782498,52.519360399],[13.3778964,52.519467799],[13.3776164,52.519564199],[13.377339,52.519682199],[13.3770764,52.519811199],[13.3767768,52.520010999],[13.3766403,52.520166099],[13.3766184,52.520201099],[13.3765316,52.520332899],[13.3764866,52.520442899],[13.3764599,52.520553899],[13.3764475,52.520634699],[13.3763841,52.520939099],[13.3763198,52.521164099],[13.3762202,52.521419199],[13.3760536,52.521627799],[13.3759333,52.521779499],[13.3758349,52.521858399],[13.3757714,52.521912899],[13.3755624,52.522053799],[13.3752777,52.522230999],[13.3749477,52.522381699],[13.3745065,52.522585799],[13.3740215,52.522753199],[13.3735194,52.522899099],[13.3731158,52.522971399],[13.3726896,52.523019999],[13.3722127,52.523057099]]}'
    multiline = shape(json.loads(line_geojson))

    # this extent contains the above feature in its North-East corner
    extent = ExtentDegrees(
        latmin=52.5098,
        latmax=52.5633,
        lonmin=13.2976,
        lonmax=13.4203,
    )

    fig = render_shapes_to_figure(
        extent, [
            (multiline, dict(
                line=dict(color='#ff0000'),
                vertex=dict(color='#00ff00'),
                vertex_fmt='o',
                ))
            ])

    assert fig.shape == (1500, 1500, 3)
