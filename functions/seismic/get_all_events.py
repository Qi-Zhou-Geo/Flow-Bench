#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-11-20
# __author__ = Qi Zhou and Sibashish Dash, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import argparse

import os
import yaml

import numpy as np
import pandas as pd


from obspy import Stream, Trace, read
from obspy.core import UTCDateTime # default is UTC+0 time zone


# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>

# import the custom functions
from functions.seismic.seismic_data_processing import load_seismic_signal
from functions.seismic.st2tr import stream_to_trace


def cache_events(idx, project_root=project_root):

    # <editor-fold desc="get event parameters">
    catchment_code_path = f"{project_root}/config/catchment_code.yaml"
    with open(catchment_code_path, "r") as f:
        config = yaml.safe_load(f)
        sac_path = config[f"glic_sac_dir"]
        event_catalog_version = config[f"event_catalog_version"]

    file_path = f"{project_root}/data/event_catalog/{event_catalog_version}"
    df = pd.read_csv(f"{file_path}", header=0)

    row_idx = df.loc[idx-1] # select row_idx
    continent = row_idx["Continent"]
    catchment = row_idx["Catchment"]
    longitude = row_idx["Longitude_sta (- denote West)"]
    latitude = row_idx["Latitude (- denote South)"]
    client = row_idx["Client"]
    seismic_network = row_idx["Network"]
    station = row_idx["Station"]
    location = row_idx["Location"]
    component = row_idx["Component"]
    sps = row_idx["SPS (Hz)"]
    distance = row_idx["Distance (km)"]
    data_start = row_idx["Start-time (UTC+0)"]
    data_end = row_idx["End-time  (UTC+0)"]
    # </editor-fold>

    # <editor-fold desc="load data and save it">
    f_min = 1
    f_max = int(sps / 2)
    extend_hour = 0.5 # left and right has half duration of the data

    event_duration = UTCDateTime(data_end) - UTCDateTime(data_start)
    extend_hour = int(extend_hour * event_duration)

    try:
        t_s = (UTCDateTime(data_start) - extend_hour).strftime("%Y-%m-%dT%H:%M:%S")
        t_e = (UTCDateTime(data_end) + extend_hour).strftime("%Y-%m-%dT%H:%M:%S")

        st = load_seismic_signal(catchment, seismic_network, station, component,
                                 t_s, t_e, f_min, f_max,
                                 remove_sensor_response=True, raw_data=False)
    except Exception as e:
        print(f"{e}")
        t_s = data_start
        t_e = data_end
        st = load_seismic_signal(catchment, seismic_network, station, component,
                                 t_s, t_e, f_min, f_max,
                                 remove_sensor_response=True, raw_data=False)

    output_path = f"{project_root}/data/seismic_temp"
    output_format = f"{str(idx).zfill(3)}-{continent}-{catchment}-{seismic_network}-{station}-{component}"
    os.makedirs(output_path, exist_ok=True)

    tr = stream_to_trace(st) # return as Trace

    # save as npz
    np.savez(f"{output_path}/{output_format}.npz",
             amp=tr.data,
             data_start=data_start,
             delta=tr.stats.delta)

    # save as st
    tr.write(f"{output_path}/{output_format}.mseed", format="MSEED")

    # </editor-fold>


def main(idx, project_root=project_root):
    cache_events(idx, project_root=project_root)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--idx", type=int, default=1)
    args = parser.parse_args()

    main(args.idx)
