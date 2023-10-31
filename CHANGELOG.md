# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.4]

### Changed
- Upgrade to Shapely 2.0
- Tolerate tables without a clear geometry type
- GDAL is now removed as a dependency, [the compatibility with Shapely was an issue](https://github.com/OSGeo/gdal/issues/3779)
- It's possible to add labels to the 2D chart

## 0.0.3
### Changed
- GDAL is now an optional dependency, under the `[geotiff]` extra
- A simple `generate_chart` helper allows the usage as a one-liner
