from setuptools import setup, find_packages


setup(
    name="geoshiny",
    version="0.0.1",
    description="GIS data rendered",
    long_description=open("README.md").read(),
    author="Jacopo Farina",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        # display, and quick troubleshooting
        "matplotlib"
        # everything math
        "numpy",
        # database access
        "asyncpg",
        # coordinate system conversion
        "pyproj",
        # geometrical operations, easy GeoJSON parsing
        # NEEDS the no-binary option, see the integration/aaa-* test for more info
        "Shapely",
    ],
    extras_require={
        # generate geoTIFF, manipulate coordinates, heavy requirement so it's optional
        "geotiff": ["GDAL"],
        "tests": [
            # tests
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            # linting
            "flake8",
            # type checking
            "mypy",
        ],s
    },
)
