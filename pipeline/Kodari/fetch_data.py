#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-04T15:08:28
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

from obspy import UTCDateTime

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
from func.seismic.remove_response import cooking_recipe
from func.download.seis import load_raw_fdsn

# catchment meta
continent = "Asia"
seis_cat = "Kodari"

# seismic meta
seis_client = "IRIS"
seis_network = "NK"
seis_station = "KKN"
seis_location = ""
seis_channel = "BHZ"


# response meta
seis_response = "xml"
sensor_type = "Guralp CMG 3T"

# event meta
starttime = UTCDateTime("2026-08-26T02:00:00")  # UTC+0
endtime = UTCDateTime("2026-08-26T08:00:00")  # UTC+0 >= "2026-08-26T06:00:00"

st_raw, inv_or_paz = load_raw_fdsn(
    # catchment meta
    continent,
    seis_cat,
    # seismic meta
    seis_client,
    seis_network,
    seis_station,
    seis_location,
    seis_channel,
    # response meta
    seis_response,
    sensor_type,
    # event meta
    starttime,
    endtime,
    # default params
    save_st=False,
    save_inv=False,
    local_dir="data/seis_raw",
)

st_cooked = cooking_recipe(st=st_raw, inv_or_paz=inv_or_paz, f_min=1, f_max=25)

# remembe to change this path for your project
st_path = Path("/Users/qizhou/#python/Flow-Alert/demo/Kodari/st_raw.mseed")
assert st_raw is not None
st_raw.write(st_path, format="MSEED")


st_path = Path("/Users/qizhou/#python/Flow-Alert/demo/Kodari/st_cooked.mseed")
st_cooked.write(st_path, format="MSEED")
st_cooked.plot()
