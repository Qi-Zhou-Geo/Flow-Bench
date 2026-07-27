#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-11-20
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import argparse

import os
import yaml

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from obspy import Stream, Trace, read
from obspy.core import UTCDateTime # default is UTC+0 time zone


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
from func.seismic.seismic_data_processing import load_seismic_signal
from func.seismic.st2tr import stream_to_trace
from func.toolkit.multi_process_archive import dump_as_row
from func.seismic.plot_obspy_st import time_series_plot

def cache_events(idx, project_root=project_root, extend_hour=0.5):

    # python starts from zero 0, but the event in Flow-Bench starts from 1
    idx = idx - 1

    # region -> get event parameters
    default_data_path = f"{project_root}/config/data_path.yaml"
    with open(default_data_path, "r") as f:
        config = yaml.safe_load(f)
        sac_path = config[f"glic_sac_dir"]
        event_catalog_version = config[f"event_catalog_version"]

    file_path = f"{project_root}/data/event_catalog/{event_catalog_version}"
    df = pd.read_csv(f"{file_path}", header=0)

    row_idx = df.loc[idx] # select row_idx
    continent = row_idx["Continent"]
    catchment = row_idx["Catchment"]
    longitude = row_idx["Longitude-Station(-denote-West)"]
    latitude = row_idx["Latitude-Station(-denote-South)"]
    client = row_idx["Client"]
    seismic_network = row_idx["Network"]
    station = row_idx["Station"]
    location = row_idx["Location"]
    component = row_idx["Component"]
    sps = row_idx["SPS(Hz)"]
    distance = row_idx["Min-Distance2DF-Channel(km)"]

    data_start = row_idx["Manually-Start-time(UTC+0)"]
    data_end = row_idx["Manually-End-time(UTC+0)"]

    ref4sta_s = row_idx["Ref-Start-time4STA(UTC+0)"]
    ref4sta_e = row_idx["Ref-End-time4STA(UTC+0)"]

    sta_s = row_idx["Start-time(UTC+0)-by-STA/LTA"]
    sta_e = row_idx["End-time(UTC+0)-by-STA/LTA"]
    # endregion


    # region -> load data and save it
    f_min = 1
    f_max = int(sps / 2)
    # extend_hour = 0.5 # left and right has half duration of the data

    event_duration = UTCDateTime(data_end) - UTCDateTime(data_start)

    if extend_hour > 1:
        # extend the data by hour
        extend_hour = extend_hour * 60 * 60 # unit by second
    else:
        # extend the data by ratio
        extend_hour = int(extend_hour * event_duration) # unit by second

    try:
        t_s = (UTCDateTime(data_start) - extend_hour).strftime("%Y-%m-%dT%H:%M:%S")
        t_e = (UTCDateTime(data_end) + extend_hour).strftime("%Y-%m-%dT%H:%M:%S")

        st = load_seismic_signal(catchment, seismic_network, station, component,
                                 t_s, t_e, f_min, f_max,
                                 remove_sensor_response=True, raw_data=False)
    except Exception as e:
        print(f"{e}")

        if catchment == "Chalk_Cliffs" and station == "gpB": # this event does not have enough data
            t_s = (UTCDateTime(data_start) - 15*60).strftime("%Y-%m-%dT%H:%M:%S")
            t_e = (UTCDateTime(data_end) + 15*60).strftime("%Y-%m-%dT%H:%M:%S")
        else:
            t_s = (UTCDateTime(data_start) - extend_hour).strftime("%Y-%m-%dT%H:%M:%S")
            t_e = (UTCDateTime(data_end) + extend_hour).strftime("%Y-%m-%dT%H:%M:%S")

        st = load_seismic_signal(catchment, seismic_network, station, component,
                                 t_s, t_e, f_min, f_max,
                                 remove_sensor_response=True, raw_data=False)

    # formate the name
    # python starts from zero 0, but the event in Flow-Bench starts from 1
    output_format = f"{str(idx+1).zfill(3)}-{continent}-{catchment}-{seismic_network}-{station}-{component}"

    output_dir = f"{current_dir}"
    output_name = "event_archive_length.txt"
    variable_str = output_format
    record = [t_s, t_e]
    dump_as_row(output_dir, output_name, variable_str, *record)

    # save as st
    output_path = f"{project_root}/data/seismic_temp/seis"
    os.makedirs(output_path, exist_ok=True)
    tr = stream_to_trace(st) # return as Trace
    tr.write(f"{output_path}/{output_format}.mseed", format="MSEED")

    # save as npz
    output_path = f"{project_root}/data/seismic_temp/npz"
    os.makedirs(output_path, exist_ok=True)
    np.savez(f"{output_path}/{output_format}.npz",
             amp=tr.data,
             data_start=data_start,
             delta=tr.stats.delta)
    # endregion

    # region -> plot the Fig
    time_markers = [data_start, data_end]
    time_markers_label = [data_start, data_end]

    fig, axes = time_series_plot(st, time_markers=time_markers, time_markers_label=time_markers_label)
    ax = axes[0]
    ax.set_ylabel(f"Amplitude\n[m/s]", fontweight='bold')
    plt.tight_layout()
    output_path = f"{project_root}/data/seismic_temp/plots"
    os.makedirs(output_path, exist_ok=True)
    plt.savefig(f"{output_path}/{output_format}.png", dpi=600, transparent=False)
    plt.close(fig)
    # endregion

def main(idx, project_root=project_root, extend_hour=6):

    cache_events(idx, project_root=project_root, extend_hour=extend_hour)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--idx", type=int, default=1)
    parser.add_argument("--extend_hour", type=int, default=6)
    args = parser.parse_args()

    main(args.idx)
