#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-10T22:28:58
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import numbers
import pandas as pd

from obspy.clients.fdsn import Client
from obspy import read, Stream, Inventory, read_inventory, UTCDateTime

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
from func.seismic.round_time import round_time
from data.meta.seis.paz_meta import load_paz

def load_raw_fdsn(continent, seis_cat, 
                  seis_client, seis_network, 
                  seis_station, seis_location, seis_channel,
                  seis_response, sensor_type,
                  starttime, endtime,
                  ):
    
    client = Client(seis_client)
    st_raw = client.get_waveforms(network=seis_network, 
                                  station=seis_station,
                                  location=seis_location, 
                                  channel=seis_channel,
                                  starttime=starttime, 
                                  endtime=endtime,
                                  attach_response=True)
    

    inv_or_paz = client.get_stations(
        starttime=starttime, 
        endtime=endtime,
        network=seis_network, 
        station=seis_station,
        location=seis_location, 
        channel=seis_channel,
        level="response",
        format="xml",
    )
    
    return st_raw, inv_or_paz


def load_raw_zenodo(continent, seis_cat, 
                  seis_client, seis_network, 
                  seis_station, seis_location, seis_channel,
                  seis_response, sensor_type,
                  starttime, endtime,
                  ):

    # set path
    year = UTCDateTime(starttime).year
    sub_folder = f"data/raw_seis/{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
    raw_st_dir = Path(project_root) / sub_folder
    all_mseed = os.listdir(raw_st_dir)

    # load all data
    st_raw = Stream()
    for file_name in all_mseed:
        if file_name.lower().endswith(".mseed"):
            raw_st_path = Path(project_root) / sub_folder / file_name
            st_raw = st_raw = read(raw_st_path)

    st_raw.merge(method=1, fill_value='latest', interpolation_samples=0)
    st_raw._cleanup()

    # trim it
    t1 = UTCDateTime(starttime)
    t2 = UTCDateTime(endtime)
    if st_raw[0].stats.starttime <= t1 < t2 <= st_raw[0].stats.endtime: # type: ignore
        st_raw.trim(UTCDateTime(starttime), UTCDateTime(endtime))
    else:
        print(
            f"Warninig. Not enough data are available in: {sub_folder}.\n"
            f"Request start: {t1}, end: {t2}\n"
            f"Available start: {st_raw[0].stats.starttime}, end {st_raw[0].stats.endtime}\n" # type: ignore
            f"All data this data are loaded.\n\n"
        )

    # load inv
    if seis_response.lower() == "xml":
        inv_or_paz = None

        inv_dir = Path(project_root) / f"data/raw_seis/{continent}/{seis_cat}"
        all_inv_dir = os.listdir(inv_dir)

        for file_name in all_inv_dir:
            if file_name.lower().endswith("xml"):
                inv_or_paz = read_inventory(f"{inv_dir}/{file_name}")

    elif seis_response.lower() in ["simulate", "manually", "do-not-need"]:
        inv_or_paz = load_paz(sensor_type) # retuen None incase there is no metadata

    else:
        raise ValueError(f"Unsupported <seis_response>: {seis_response}, <sensor_type>: {sensor_type}")

    return st_raw, inv_or_paz


def cooking_recipe(st, inv_or_paz, f_min=1, f_max=25):
    
    st_copy = st.copy()
    
    st_copy.merge(method=1, fill_value='latest', interpolation_samples=0)
    st_copy._cleanup()
    st_copy.detrend('linear')
    st_copy.detrend('demean')
    st_copy.taper(max_percentage=0.01)
    
    pre_filt = (0.5 * f_min, f_min, f_max, 1.2 * f_max)
    if isinstance(inv_or_paz, Inventory) is True:
        st_copy = st_copy.remove_response(output="VEL", pre_filt=pre_filt, water_level=60, inventory=inv_or_paz)
    elif isinstance(inv_or_paz, dict) is True:
        st_copy = st_copy.simulate(paz_remove=inv_or_paz, paz_simulate=None, remove_sensitivity=True, pre_filt=pre_filt)
    elif isinstance(inv_or_paz, numbers.Number) is True:
        st_copy[0].data = st_copy[0].data / inv_or_paz
    else:
        raise ValueError(f"Unsupported inv_or_paz: {inv_or_paz}")
        
    st_copy.filter("bandpass", freqmin=f_min, freqmax=f_max)
    st_copy.detrend('linear')
    st_copy.detrend('demean')
    
    return st_copy


def download_seis(continent, seis_cat, 
                  seis_client, seis_network, 
                  seis_station, seis_location, seis_channel,
                  seis_response, sensor_type,
                  starttime, endtime,
                  
                  buffer_time=3,
                  f_min=1, f_max=25,
                  ):

    starttime = UTCDateTime(starttime) - buffer_time * 3600
    starttime = UTCDateTime(round_time(starttime))
    
    endtime = UTCDateTime(endtime) + buffer_time * 3600
    endtime = UTCDateTime(round_time(endtime))
    
    if pd.isna(seis_location) is True:
        seis_location = ""
    
    if seis_client in ["Private", "Zenodo"]:
        st_raw, inv_or_paz = load_raw_zenodo(continent, seis_cat, 
                  seis_client, seis_network, 
                  seis_station, seis_location, seis_channel,
                  seis_response, sensor_type,
                  starttime, endtime,
                  )
    else:
        st_raw, inv_or_paz = load_raw_fdsn(continent, seis_cat, 
                  seis_client, seis_network, 
                  seis_station, seis_location, seis_channel,
                  seis_response, sensor_type,
                  starttime, endtime,
                  )

    st_cooked = cooking_recipe(st=st_raw, inv_or_paz=inv_or_paz, f_min=f_min, f_max=f_max)

    return st_raw, st_cooked
