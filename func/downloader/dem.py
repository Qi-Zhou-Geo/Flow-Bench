#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-10T09:05:51
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import yaml
import requests

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion


def load_key():
    
    try:
        key_path = Path(project_root) / "config/OpenTopography_key.yml"
        with open(key_path, "r") as f:
            config = yaml.safe_load(f)
            API_Key = config[f"API_Key"]
    except FileNotFoundError:
        raise ValueError("Please regeist your OpenTopography account and downlaod your key.\nURL<https://portal.opentopography.org/login>")
        
    return API_Key


def load_dem_range(seis_cat, dem_resolution):
    
    try:
        key_path = Path(project_root) / f"data/meta/dem/{seis_cat}_{dem_resolution}.yml"
        with open(key_path, "r") as f:
            config = yaml.safe_load(f)
            
            dem_west_lon = config["dem_west_lon"]
            dem_south_lat = config["dem_south_lat"]
            dem_east_lon = config["dem_east_lon"]
            dem_north_lat = config["dem_north_lat"]
            
    except FileNotFoundError:
        raise ValueError("Please check the dem metadata.")
    
    return dem_west_lon, dem_south_lat, dem_east_lon, dem_north_lat


def define_copernicus_params(seis_cat, dem_resolution):

    API_KEY = load_key()
    temp = load_dem_range(seis_cat, dem_resolution)
    dem_west_lon, dem_south_lat, dem_east_lon, dem_north_lat = temp

    url = "https://portal.opentopography.org/API/globaldem"

    west = min(dem_west_lon, dem_east_lon) # minimum longitude
    east = max(dem_west_lon, dem_east_lon) # maximum longitude
    south = min(dem_south_lat, dem_north_lat) # minimum latitude
    north = max(dem_south_lat, dem_north_lat) # maximum latitude

    params = {
        "demtype": f"COP{int(dem_resolution)}", # COP30 = Copernicus GLO-30 DEM
        
        "west": west, 
        "east": east, 
        
        "south": south,
        "north": north,

        "outputFormat": "GTiff", # data format
        "API_Key": API_KEY,
    }

    return url, params


def download_dem(seis_cat, dem_resolution):
    
    # (1) prepaer the params
    url, params = define_copernicus_params(seis_cat, dem_resolution)

    # (2) buidl the request
    dem = requests.get(url, params=params)
    dem.raise_for_status()

    # (3) save to local
    dem_path = Path(project_root) / f"data/raw_geo/{seis_cat}/{seis_cat}_{dem_resolution}.tif"
    dem_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dem_path, "wb") as f:
        f.write(dem.content)
    
    return dem


def usage():
    seis_cat, dem_resolution = "Illgraben", 30
    download_dem(seis_cat, dem_resolution)
    