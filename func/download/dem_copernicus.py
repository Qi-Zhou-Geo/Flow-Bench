#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-24T17:16:11
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import yaml
import zipfile
import shutil
import requests

import numpy as np

from shapely.geometry import box, shape


from urllib.parse import urlparse

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


# public for Copernicus and ASF
def load_key(key_name):

    try:
        key_path = Path(project_root) / "config/dem_key.yml"
        with open(key_path, "r") as f:
            config = yaml.safe_load(f)
            API_Key = config[key_name]
    except FileNotFoundError:
        raise ValueError(
            "Please regeist your account and downlaod your key.\nURL<https://portal.opentopography.org/login>\nhttps://urs.earthdata.nasa.gov/home\n\n"
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


# private for Copernicus
def define_copernicus_params(version, seis_cat, dem_resolution):

    API_KEY = load_key("Copernicus")
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


# private for ASF
def define_asf_params(version, seis_cat, dem_resolution):

    API_KEY = load_key("ASF")

    west, south, east, north = load_dem_range(version, seis_cat, dem_resolution)
    bounds = (
        min(west, east),
        min(south, north),
        max(west, east),
        max(south, north),
    )

    url = "https://api.daac.asf.alaska.edu/services/search/param"

    params = {
        "platform": "ALOS",
        "processingLevel": "RTC_HI_RES",
        "intersectsWith": box(*bounds).wkt,
        "output": "geojson",
        "maxResults": 250,
    }

    headers = {"Authorization": f"Bearer {API_KEY}"}

    return url, params, headers, bounds


def select_asf_products(catalog, bounds, max_scenes=8):
    remaining = box(*bounds)
    original_area = remaining.area
    candidates = []
    for item in catalog.get("features", []):
        props = item.get("properties", {})
        if props.get("url") and item.get("geometry"):
            candidates.append((props, shape(item["geometry"])))
    selected = []
    while candidates and len(selected) < max_scenes:
        index = max(range(len(candidates)), key=lambda i: remaining.intersection(candidates[i][1]).area)
        props, footprint = candidates.pop(index)
        if remaining.intersection(footprint).area == 0:
            break
        selected.append(props)
        remaining = remaining.difference(footprint)
        if remaining.area / original_area < 1e-6:
            return selected
    raise ValueError("ASF scenes do not cover the DEM bounds; increase max_scenes or use Copernicus")


def download_file(url, target, session=None, params=None):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    try:
        with (session or requests).get(url, params=params, stream=True, timeout=(30, 600)) as response:
            if not response.ok:
                # Do not include a request URL containing the API key in errors.
                raise RuntimeError(f"Download failed: HTTP {response.status_code} from {urlparse(url).hostname}")
            size = 0
            with partial.open("wb") as handle:
                for chunk in response.iter_content(1024 * 1024):
                    handle.write(chunk)
                    size += len(chunk)
            expected = response.headers.get("Content-Length")
            if expected and not response.headers.get("Content-Encoding") and size != int(expected):
                raise RuntimeError("Incomplete download")
        partial.replace(target)
    except requests.RequestException as error:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"Download connection failed at {urlparse(url).hostname}: {type(error).__name__}") from None
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return target


def download_dem_from_asf(version, seis_cat, dem_resolution):

    # (1) prepare the parameters
    url, params, headers, bounds = define_asf_params(version, seis_cat, dem_resolution)

    # (2) search and select scenes covering the DEM region
    response = requests.get(url, params=params, timeout=120)
    response.raise_for_status()
    products = select_asf_products(response.json(), bounds)

    # (3) download and save to local
    directory = Path(project_root) / f"data/hydro_raw/{seis_cat}"
    directory.mkdir(parents=True, exist_ok=True)

    dem_paths = []

    with requests.Session() as session:
        session.headers.update(headers)

        for product in products:
            archive = directory / Path(urlparse(product["url"]).path).name

            if not archive.exists():
                download_file(product["url"], archive, session=session)

            # (4) extract the elevation files
            with zipfile.ZipFile(archive) as bundle:
                for name in bundle.namelist():
                    if not name.lower().endswith(".dem.tif"):
                        continue

                    dem_path = directory / archive.stem / Path(name).name
                    dem_path.parent.mkdir(parents=True, exist_ok=True)

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
