# Note
- Author: Qi Zhou
- Last update: 2026-04-16

## Python Env.
- whitebox-gmt.yml
prepare the env as this [guideline](https://github.com/Qi-Zhou-Geo/Flow-Bench/blob/main/docs/prepare_env.md).


## File structure
This folder contains the following files:

- point
  - the .shp seismic stations
  - the .shp outlet, you need to define this manually via QGIS and make the CRS same as your DEM
- polygon
  - the .shp catchment boundary
  - the cut_dem.shp, if your original dem is too big, use this as mask to cut your "big" dem
- polyline
  - the .shp stream/channel, you may see raw_streams.shp and streams.shp, the first is from the code and later is manually post-processed
- raster
  - the .tiff orthophoto images or dem files

## Reproducibility
If you change the default paramsters,
- threshold=5000
- snap_dist=2

please explicitly point out.