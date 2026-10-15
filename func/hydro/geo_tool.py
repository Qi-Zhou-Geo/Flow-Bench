#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-25T13:41:36
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import geopandas as gpd
from shapely.geometry import Point, box

import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject


# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion


def point2gpd(
    lon,  # float, unit by degree
    lat,  # float, unit by degree
    save_path=None,
    crs="EPSG:4326",
):

    gpd_point = gpd.GeoDataFrame(
        {"ID": [1]},
        geometry=[Point(lon, lat)],
        crs=crs,
    )

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        gpd_point.to_file(save_path)

    return gpd_point


def project_dem(dem_path, projected_dem_path, resolution, crs=None):

    with rasterio.open(dem_path) as src:
        # estimate the crs for the projected DEM
        if crs is None:
            crs = gpd.GeoSeries([box(*src.bounds)], crs=src.crs).estimate_utm_crs()

        transform, width, height = calculate_default_transform(
            src.crs,
            crs,
            src.width,
            src.height,
            *src.bounds,
            resolution=resolution,
        )

        # metadata
        profile = src.profile.copy()
        profile.update(
            crs=crs,
            transform=transform,
            width=width,
            height=height,
            count=1,
            dtype="float32",
            nodata=-9999,
        )

        # save to local
        projected_dem_path = Path(projected_dem_path)
        projected_dem_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(projected_dem_path, "w", **profile) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                resampling=Resampling.bilinear,
            )

    print(f"Done projection.\nProjected DEM was saved at >> {projected_dem_path}\nCRS >> {crs}\n\n")
