#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-25T13:55:00
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from shapely import get_coordinates
from shapely.geometry import Point
from rasterio.mask import mask


# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion


def calculate_geometry(basin, channel):

    # Area and lengths: km² and km
    A = basin.area / 1e6
    Lc = channel.length / 1000

    head = Point(channel.coords[0])
    outlet = Point(channel.coords[-1])
    Lv = head.distance(outlet) / 1000

    boundary_xy = get_coordinates(basin.boundary)
    Lb = (
        np.hypot(
            boundary_xy[:, 0] - outlet.x,
            boundary_xy[:, 1] - outlet.y,
        ).max()
        / 1000
    )

    if min(A, Lc, Lv, Lb) <= 0:
        raise ValueError("Area and lengths must be positive.")

    output = {
        "A_km**2": A,
        ##
        "Lc_km": Lc,
        "Lv_km": Lv,
        "Lb_km": Lb,
        ##
        "P_sin": Lc / Lv,
        "R_e": 2 * np.sqrt(A / np.pi) / Lb,
    }

    return output


def calculate_relief(projected_dem_path, basin, Lb_km):

    with rasterio.open(projected_dem_path) as src:
        elevation, _ = mask(
            src,
            [basin.__geo_interface__],
            indexes=1,
            crop=True,
            filled=False,
        )

    values = elevation.compressed()
    values = values[np.isfinite(values)]

    if values.size == 0:
        raise ValueError("No valid elevations inside the catchment.")
    if Lb_km <= 0:
        raise ValueError("Basin length must be positive.")

    h_min = float(values.min())
    h_max = float(values.max())

    output = {
        "h_min_m": h_min,
        "h_max_m": h_max,
        "R_r": (h_max - h_min) / (Lb_km * 1000),
    }

    return output


def calculate_station_stats(projected_dem_path, channel, stations, n=1, crs="EPSG:4326"):

    if not np.isfinite(n) or n <= 0:
        raise ValueError("n must be positive.")

    # (1) channel chainage and elevations
    coords = np.asarray(channel.coords)
    s = np.r_[
        0,
        np.cumsum(np.hypot(np.diff(coords[:, 0]), np.diff(coords[:, 1]))),
    ]

    with rasterio.open(projected_dem_path) as src:
        dem_crs = src.crs
        resolution = max(abs(value) for value in src.res)

        samples = list(src.sample(coords, indexes=1, masked=True))
        h = np.ma.vstack(samples).astype(float).filled(np.nan).ravel()  # type: ignore

    # (2) stations: name, longitude, latitude
    results = pd.DataFrame(stations, columns=["station", "lon", "lat"])

    points = gpd.GeoSeries(gpd.points_from_xy(results.lon, results.lat), crs=crs).to_crs(dem_crs)

    results["d_m"] = points.distance(channel)
    results["s_m"] = [channel.project(point) for point in points]
    results["n"] = n

    results["upstream_s_m"] = results["s_m"] - n * results["d_m"]
    results["downstream_s_m"] = results["s_m"] + n * results["d_m"]

    results["hu_m"] = np.nan
    results["hl_m"] = np.nan
    results["Rs"] = np.nan
    results["status"] = "ok"

    # (3) slope within ±n × d of the nearest channel point
    for index, station in results.iterrows():
        su = station["upstream_s_m"]
        sl = station["downstream_s_m"]

        if station["d_m"] <= 1e-9:
            status = "zero_station_distance"
        elif su < 0 or sl > s[-1]:
            status = "window_outside_channel"
        elif sl - su < resolution:
            status = "window_below_DEM_spacing"
        else:
            hu, hl = np.interp([su, sl], s, h)

            if np.isfinite(hu) and np.isfinite(hl):
                results.loc[index, "hu_m"] = hu
                results.loc[index, "hl_m"] = hl
                results.loc[index, "Rs"] = (hu - hl) / (sl - su)
                status = "ok"
            else:
                status = "missing_elevation"

        results.loc[index, "status"] = status

    return results


def calculate_catchment(
    projected_dem_path,
    catchment_path,
    channel_path,
    stations=(),
    n=1,
):

    # (1) load the files in the DEM's projected CRS
    with rasterio.open(projected_dem_path) as src:
        dem_crs = src.crs

    if dem_crs is None or not dem_crs.is_projected or not np.isclose(dem_crs.linear_units_factor[1], 1):
        raise ValueError("The DEM CRS must use metres.")

    catchment = gpd.read_file(catchment_path)
    channel = gpd.read_file(channel_path)

    # These files were generated from the projected DEM
    if catchment.crs is None:
        catchment = catchment.set_crs(dem_crs)
    if channel.crs is None:
        channel = channel.set_crs(dem_crs)

    catchment = catchment.to_crs(dem_crs)
    channel = channel.to_crs(dem_crs)

    if len(channel) != 1 or channel.geometry.iloc[0].geom_type != "LineString":  # type: ignore
        raise ValueError("Provide one continuous main channel, ordered head → outlet.")

    basin = catchment.geometry.union_all()
    main_channel = channel.geometry.iloc[0]

    # (2) calculate the three parts
    geometry = calculate_geometry(basin, main_channel)

    relief = calculate_relief(
        projected_dem_path,
        basin,
        geometry["Lb_km"],
    )

    station_metrics = calculate_station_stats(
        projected_dem_path,
        main_channel,
        stations,
        n=n,
    )

    return geometry, relief, station_metrics


def usage():

    projected_dem_path = "/Users/qizhou/#python/Flow-Bench-geo/cache/hydro/ILLgraben/Illgraben_30_UTM.tif"
    catchment_path = "/Users/qizhou/#python/Flow-Bench-geo/cache/hydro/ILLgraben/catchment.shp"
    channel_path = "/Users/qizhou/#python/Flow-Bench-geo/cache/hydro/Illgraben/main_channel.shp"

    stations = [
        ("9J.IGB02", 46.286374, 7.627810),
    ]

    geometry, relief, station_metrics = calculate_catchment(
        projected_dem_path,
        catchment_path,
        channel_path,
        stations=stations,
        n=1,
    )

    print(pd.Series(geometry).round(4))
    print(pd.Series(relief).round(4))
    print(station_metrics)
