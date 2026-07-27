#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import yaml

import argparse

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
# from brokenaxes import brokenaxes

from scipy.stats import linregress
from scipy.stats import t as student_t  # Student's t-distribution
from scipy.stats import gaussian_kde

from obspy import Stream, Trace, read
from obspy.core import UTCDateTime  # default is UTC+0 time zone

from scipy.signal import hilbert

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
from func.seismic.plot_obspy_st import time_series_plot
from func.seismic.generate_seismic_trace import create_trace
from func.seismic.signal_denoising import st_denoising
from func.labeling_debris_flow.signal_sta_lta import sta_lta_timing
from func.seismic.plot_obspy_st import time_series_plot

dict_time = {
    # Illgraben
    2: "2013-07-29T06:15:00_2013-07-29T09:00:00",
    3: "2013-07-29T08:15:00_2013-07-29T10:30:00",
    4: "2013-07-29T10:00:00_2013-07-29T12:20:00",

    # 17: "2014-07-08T04:00:00_2014-07-08T09:30:00",
    17: "2014-07-08T08:15:00_2014-07-08T14:00:00",

    19: "2014-07-20T19:00:00_2014-07-20T23:00:00",
    20: "2014-07-20T22:00:00_2014-07-21T01:30:00",
    23: "2014-07-28T21:00:00_2014-07-29T02:20:00",
    24: "2014-07-29T01:45:00_2014-07-29T08:00:00",

    39: "2019-06-10T16:00:00_2019-06-10T20:00:00",

    49: "2019-08-11T15:00:00_2019-08-11T19:00:00",
    57: "2020-06-16T21:00:00_2020-06-17T01:30:30",
    58: "2020-06-17T00:30:00_2020-06-17T03:40:00",
    59: "2020-06-17T02:40:00_2020-06-17T08:00:00",
    # Chalk Cliff
    76: "2020-06-19T09:00:00_2020-06-19T10:45:00",
    # Adams
    90: "2012-07-25T03:45:00_2012-07-25T05:00:00",
    # Hood
    92: "2015-08-19T19:00:00_2015-08-20T01:00:00",
    94: "2015-08-22T23:00:00_2015-08-23T02:00:00",
    # Joffre
    95: "2019-05-13T13:00:00_2019-05-13T16:00:00",
    96: "2019-05-16T15:00:00_2019-05-16T17:00:00",
    # Shasta
    102: "2021-07-01T20:00:00_2021-07-02T04:00:00",
    # St_Helens
    109: "2014-10-22T12:00:00_2014-10-22T23:00:00",
    110: "2015-08-14T20:00:00_2015-08-14T23:30:00",
    111: "2015-09-17T22:00:00_2015-09-18T01:00:00",
    # Oso
    112: "2014-03-22T17:00:00_2014-03-22T18:30:00",
    # Redoubt
    116: "2009-03-26T15:00:00_2009-03-26T17:20:00",
    # Shishaldin
    119: "2019-10-28T23:55:00_2019-10-29T01:30:00",
    # Villa_Santa
    120: "2017-12-16T11:00:00_2017-12-16T13:00:00",
    # Tianmo
    121: "2020-06-19T09:00:00_2020-06-19T10:45:00",
    122: "2020-06-19T11:00:00_2020-06-19T13:00:00",
    123: "2020-06-26T17:00:00_2020-06-26T22:00:00",
    124: "2020-06-26T21:00:00_2020-06-26T22:30:00",
    125: "2020-06-26T22:00:00_2020-06-27T02:30:00",
    126: "2020-06-27T13:00:00_2020-06-27T15:30:00",
    127: "2020-06-27T15:00:00_2020-06-27T19:0:00",
    128: "2020-06-27T18:00:00_2020-06-27T23:00:00",
    134: "2020-09-25T05:00:00_2020-09-25T08:00:00",
}


def set_st_path():

    # set the data path
    st_path = f"{project_root}/data/seismic_temp/seis"
    st_file_list = os.listdir(st_path)
    st_file_list = sorted(st_file_list)
    if '.DS_Store' in st_file_list:
        st_file_list.remove('.DS_Store')

    return st_file_list


def trim_stream(st,
                data_start,
                data_end,
                short_window=180,
                long_window=1800):

    # do not use too many data
    tr = st.copy()
    t1 = UTCDateTime(data_start) - long_window * 2
    t2 = UTCDateTime(data_end) + long_window * 2

    tr.trim(t1, t2)

    return tr


def load_pre_processed_st(idx, st_file_list, short_window, long_window, f_min=5, f_max=25):
    # load the pre-processed (detrean, demean, remove sensor response) seismic data
    st_file = st_file_list[idx]  # idx starts from zero 0
    st = read(f"{project_root}/data/seismic_temp/seis/{st_file}")
    st = trim_stream(idx, st, short_window, long_window)

    # only focus on the 5 - 25 Hz
    st.filter("bandpass", freqmin=f_min, freqmax=f_max)
    st.detrend('linear')
    st.detrend('demean')

    keys = list(dict_time.keys())

    if int(idx + 1) in keys:  # back to start=1
        s_e = dict_time.get(idx + 1)
        print(s_e)
        t_s, t_e = s_e.split("_")
        st.trim(UTCDateTime(t_s), UTCDateTime(t_e))

    return st


def find_st_timing(st, window_size, window_ovelap, denoising_method,
                   short_window, long_window, ratio_on, ratio_off,
                   f_min, f_max,
                   output_name):

    # denoise the seismic trace using a RMS sliding window
    t_value, x_value, low_sampling_rate, denoised_st = st_denoising(st, window_size, window_ovelap, denoising_method)

    # start the STA/LTA
    st_cft_on, st_cft_off, time_on, time_off = sta_lta_timing(st=denoised_st,
                                                              short_window=short_window, long_window=long_window,
                                                              ratio_on=ratio_on, ratio_off=ratio_off)
    st_cft_on[0].stats.location = "on"
    st_cft_off[0].stats.location = "off"

    st_file_list = Stream()
    st_file_list += denoised_st
    st_file_list += st_cft_on
    st_file_list += st_cft_off

    time_markers = []
    time_markers_label = []
    for i in time_on:
        time_markers.append(i)
        time_markers_label.append(f"on_{i}")

    for i in time_off:
        time_markers.append(i)
        time_markers_label.append(f"off_{i}")

    # plot it
    fig, axes = time_series_plot(st_file_list, time_markers=time_markers, time_markers_label=time_markers_label)
    y_label = ["Amplitude\n[m/s]", "STA/LTA Ratio\n[forward]", "STA/LTA Ratio\n[backward]"]

    for idx, (ax, label) in enumerate(zip(axes, y_label)):
        ax.set_ylabel(f"{label}", fontweight='bold')

        if idx == 0:
            ax.set_title(label=f"f_min={f_min}, f_max={f_max}"
                               f"\nratio_on={ratio_on}, ratio_off={ratio_off}", fontsize=7, fontweight='bold')
        else:
            ax.axhline(y=ratio_on, color="red", ls="--", lw=1, alpha=0.5, label=f"ratio_on={ratio_on}")
            ax.axhline(y=ratio_off, color="red", ls="-", lw=1, alpha=0.5, label=f"ratio_off={ratio_off}")

    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0.3)
    output_path = f"./plots"
    os.makedirs(output_path, exist_ok=True)
    plt.savefig(f"{output_path}/{output_name}.png", dpi=600, transparent=False)
    plt.close(fig)


def main(idx,
         st_file_list,
         short_window=180, # by seconds
         long_window=1800,
         ratio_on=1.5,
         ratio_off=1.5,
         window_size=1,
         window_ovelap=0,
         denoising_method="RMS",
         f_min=5, # by Hz
         f_max=25):

    # python starts from zero 0, but the event in Flow-Bench starts from 1
    idx = idx - 1

    # <editor-fold desc="get event parameters">
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
    # </editor-fold>


    # load the pre-processed (detrean, demean, remove sensor response) seismic data
    st_file = st_file_list[idx]
    st = read(f"{project_root}/data/seismic_temp/seis/{st_file}")

    if ref4sta_s == "do-not-need":
        # for the cases that with single event
        st = trim_stream(st, data_start, data_end, short_window, long_window)
    else:
        # for the cases that with multiple events together
        st.trim(UTCDateTime(ref4sta_s), UTCDateTime(ref4sta_e))


    # only focus on the 5 - 25 Hz
    st.filter("bandpass", freqmin=f_min, freqmax=f_max)
    st.detrend('linear')
    st.detrend('demean')

    # start the func.
    output_name = st_file.split(".")[0]
    find_st_timing(st, window_size, window_ovelap, denoising_method,
                   short_window, long_window, ratio_on, ratio_off,
                   f_min, f_max,
                   output_name)

if __name__ == "__main__":
    # sinfo -n node[501-514] -N --Format="Nodelist,CPUsState,AllocMem,Memory,GresUsed,Gres"
    parser = argparse.ArgumentParser(description='input parameters')

    parser.add_argument("--idx", default=0, type=int)

    args = parser.parse_args()

    # start the labeling
    st_file_list = set_st_path()
    short_window, long_window, ratio_on, ratio_off = 180, 1800, 3, 2

    main(args.idx, st_file_list, short_window, long_window, ratio_on, ratio_off)

    print(f"Done! {args.idx}")
