#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-24T17:07:31
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import yaml
import requests

import numpy as np

from shapely.geometry import box  # , #shape


# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion

# import the custom functions
from func.toolkit.xlsx_to_txt import xlsx2txt


def load_key():

    try:
        key_path = Path(project_root) / "config/dem_key.yml"
        with open(key_path, "r") as f:
            config = yaml.safe_load(f)
            API_Key = config["API_Key"]
    except FileNotFoundError:
        raise ValueError(
            "Please regeist your OpenTopography account and downlaod your key.\nURL<https://portal.opentopography.org/login>"
        )

    return API_Key


def load_dem_range(version, seis_cat, dem_resolution):

    try:
        input_xlsx_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{version}.xlsx"
        output_txt_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{version}.txt"
        column_s, column_e = 1, 35 + 1  # from DEM-Resolution to Outlet-Lat
        df = xlsx2txt(input_xlsx_path, output_txt_path, column_s, column_e)

        selected_id = np.where(df["seis_cat"] == seis_cat)[0][0]

        dem_west_lon = df["dem_west_lon"][selected_id]
        dem_south_lat = df["dem_south_lat"][selected_id]
        dem_east_lon = df["dem_east_lon"][selected_id]
        dem_north_lat = df["dem_north_lat"][selected_id]

        archived_res = df["dem_resolution"][selected_id]
        msg = f"Request dem_resolution != res.\ndem_resolution >> {dem_resolution}\narchived_res >> {archived_res}\n\n"
        assert dem_resolution == archived_res, msg

    except FileNotFoundError:
        raise ValueError("Please check the dem metadata.")

    return dem_west_lon, dem_south_lat, dem_east_lon, dem_north_lat


def define_copernicus_params(version, seis_cat, dem_resolution):

    API_KEY = load_key()
    temp = load_dem_range(version, seis_cat, dem_resolution)
    dem_west_lon, dem_south_lat, dem_east_lon, dem_north_lat = temp

    url = "https://portal.opentopography.org/API/globaldem"

    west = min(dem_west_lon, dem_east_lon)  # minimum longitude
    east = max(dem_west_lon, dem_east_lon)  # maximum longitude
    south = min(dem_south_lat, dem_north_lat)  # minimum latitude
    north = max(dem_south_lat, dem_north_lat)  # maximum latitude

    params = {
        "demtype": f"COP{int(dem_resolution)}",  # COP30 = Copernicus GLO-30 DEM
        "west": west,
        "east": east,
        "south": south,
        "north": north,
        "outputFormat": "GTiff",  # data format
        "API_Key": API_KEY,
    }

    return url, params


def download_dem_from_copernicus(version, seis_cat, dem_resolution):

    # (1) prepaer the params
    url, params = define_copernicus_params(version, seis_cat, dem_resolution)

    # (2) buidl the request
    dem = requests.get(url, params=params)
    dem.raise_for_status()

    # (3) save to local
    dem_path = Path(project_root) / f"data/hydro_raw/{seis_cat}/{seis_cat}_{dem_resolution}.tif"
    dem_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dem_path, "wb") as f:
        f.write(dem.content)

    return dem


def download_dem_from_asf(version, seis_cat, dem_resolution):

    # (1) prepare the parameters
    bounds = load_dem_range(version, seis_cat, dem_resolution)

    url = "https://api.daac.asf.alaska.edu/services/search/param"
    params = {
        "platform": "ALOS",
        "processingLevel": "RTC_HI_RES",
        "intersectsWith": box(*bounds).wkt,
        "output": "geojson",
        "maxResults": 250,
    }

    directory = Path(project_root) / f"data/hydro_raw/{seis_cat}"
    directory.mkdir(parents=True, exist_ok=True)

    # (2) search and select scenes covering the DEM region
    response = requests.get(url, params=params, timeout=120)
    response.raise_for_status()
    products = select_asf_products(response.json(), bounds)

    # (3) download archives and extract DEM files
    dem_paths = []

    with requests.Session() as session:
        for product in products:
            url = product["url"]
            archive = directory / Path(urlparse(url).path).name

            if not archive.exists():
                earthdata_login(session, url)
                download_file(url, archive, session=session)

            with zipfile.ZipFile(archive) as bundle:
                for name in bundle.namelist():
                    if name.lower().endswith(".dem.tif"):
                        dem_path = directory / Path(name).name

                        with bundle.open(name) as source, dem_path.open("wb") as target:
                            shutil.copyfileobj(source, target)

                        dem_paths.append(dem_path)

    if not dem_paths:
        raise ValueError("No DEM files found in the downloaded archives.")

    return dem_paths


def usage():
    version = "essd"
    seis_cat, dem_resolution = "Illgraben", 30
    download_dem_from_copernicus(version, seis_cat, dem_resolution)
