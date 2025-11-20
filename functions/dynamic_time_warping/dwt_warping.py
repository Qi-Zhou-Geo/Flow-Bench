#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou and Sibashish Dash, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import os
import array
import yaml

import numpy as np
import pandas as pd
from tqdm import tqdm

from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.signal import medfilt

from dtaidistance import dtw
from dtaidistance import dtw_visualisation as dtwvis

from obspy import read, Trace, Stream, read_inventory, signal
from obspy.core import UTCDateTime  # default is UTC+0 time zone

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path

current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys

sys.path.append(str(project_root))
# </editor-fold>

# import the custom functions
from functions.seismic.st2tr import stream_to_trace
from functions.seismic.signal_denoising import st_denoising
from functions.seismic.generate_seismic_trace import create_trace
from pipeline.fit_slope.main import set_st_path

def min_max_normalize(x):
    '''
    Normalize the 1D array to 0-1

    Args:
        x:

    Returns:

    '''
    x_normalized = (x - np.min(x)) / (np.max(x) - np.min(x))

    return x_normalized

def load_and_smooth_single_trace(idx, window_size=10, window_overlap=0, denoising_method="RMS", time_type="STA/LTA"):

    # <editor-fold desc="prepare data">
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
    type_source = row_idx["Type(debris-flow=DF)"]

    data_start = row_idx["Manually-Start-time(UTC+0)"]
    data_end = row_idx["Manually-End-time(UTC+0)"]

    ref4sta_s = row_idx["Ref-Start-time4STA(UTC+0)"]
    ref4sta_e = row_idx["Ref-End-time4STA(UTC+0)"]

    sta_s = row_idx["Start-time(UTC+0)-by-STA/LTA"]
    sta_e = row_idx["End-time(UTC+0)-by-STA/LTA"]
    # </editor-fold>


    output_name = f"{idx+1:03d}-{continent}-{catchment}-{seismic_network}-{station}-{component}"
    st = read(f"{project_root}/data/seismic_temp/seis/{output_name}.mseed")

    row_idx = df.loc[idx]  # select row_idx
    data_start = row_idx["Manually-Start-time(UTC+0)"]
    data_end = row_idx["Manually-End-time(UTC+0)"]
    sta_s = row_idx["Start-time(UTC+0)-by-STA/LTA"]
    sta_e = row_idx["End-time(UTC+0)-by-STA/LTA"]

    if time_type == "STA/LTA":
        t1, t2 = sta_s, sta_e
        st.trim(UTCDateTime(t1), UTCDateTime(t2))
    elif time_type == "manually_labeled":
        t1, t2 = data_start, data_end
        st.trim(UTCDateTime(t1), UTCDateTime(t2))
    elif time_type == "extened_time":

        source = row_idx["Type(debris-flow=DF)"]
        if any(i in source for i in "0123456789"):
            # for the case two events too close each other
            t1, t2 = sta_s, sta_e
            print(f"\nfor the case two events too close each other.\n"
                  f"{output_name, sta_s, sta_e}")
        else:
            # for the case without close neighbor events
            t1, t2 = sta_s, sta_e
            extened_time = (UTCDateTime(t2) - UTCDateTime(t1)) * 0.25

            t1, t2 = UTCDateTime(t1) - extened_time, UTCDateTime(t2) + extened_time

        st.trim(UTCDateTime(t1), UTCDateTime(t2))

    else:
        pass

    # denoise and convert to a new trace
    t_value, x_value, low_sampling_rate, denoised_st = st_denoising(st, window_size, window_overlap, denoising_method)
    tr = create_trace(data=x_value, start_time=t_value[0], data_sampling_rate=low_sampling_rate, ref_st=st)
    tr = stream_to_trace(st=tr)

    return tr

def load_and_smooth_all_traces(window_size=10, window_overlap=0, denoising_method="RMS", time_type="STA/LTA"):

    # <editor-fold desc="get event parameters">
    import yaml
    default_data_path = f"{project_root}/config/data_path.yaml"
    with open(default_data_path, "r") as f:
        config = yaml.safe_load(f)
        sac_path = config[f"glic_sac_dir"]
        event_catalog_version = config[f"event_catalog_version"]

    file_path = f"{project_root}/data/event_catalog/{event_catalog_version}"
    df = pd.read_csv(f"{file_path}", header=0)
    # </editor-fold>


    traces_list = []
    unique_id_list = []

    for idx in tqdm(range(len(df)), desc="Processing <load_and_smooth_all_traces>", file=sys.stdout):

        tr = load_and_smooth_single_trace(idx, window_size, window_overlap, denoising_method, time_type)
        traces_list.append(tr)

        row_idx = df.loc[idx]
        station = row_idx["Station"]
        distance = row_idx["Min-Distance2DF-Channel(km)"]
        type_source = row_idx["Type(debris-flow=DF)"]
        catchment = row_idx["Catchment"]

        unique_id = None
        if station in ["IGB02", "ILL02", "ILL12"]:
            source = type_source.split("_")[1]
            if source == "WSL":
                unique_id = f"WSL-recorded-{distance}"
            elif source == "GFZ":
                unique_id = f"GFZ-labeled-{distance}"
            else:
                print("error")
        else:
            unique_id = f"{catchment}-{station}-{distance}"

        unique_id_list.append(unique_id)


    return traces_list, unique_id_list

def calculate_dwt_matrix(traces_amp):

    num_of_sequence = len(traces_amp)
    distance_matrix = np.zeros((num_of_sequence, num_of_sequence))

    # loop and create the matrix
    for i in range(num_of_sequence):
        for j in range(i + 1, num_of_sequence):  # avoid redundant calculations

            # dtw.distance or dtw.distance_fast (c-based),
            # return a bounded distance, 0 means that two instances are equal
            distance = dtw.distance_fast(traces_amp[i], traces_amp[j])
            distance_matrix[i, j] = distance
            distance_matrix[j, i] = distance

    return distance_matrix

def generate_amp_index(amp):

    # smmoth the data by 12 their neighbors to avoid the signle max
    # like the case 2019-10-15T16:00:00 case
    amp = medfilt(amp, kernel_size=19)
    max_idx = np.argmax(amp)
    amp_index = np.arange(-max_idx, len(amp) - max_idx)

    return amp_index

def cluster_target(target_trace, template_labels, template_traces):

    template_traces = np.array(template_traces, dtype=object)
    unique_labels = np.unique(template_labels)
    temp_target_label = {} # create a empty dict.

    for label in unique_labels:
        index = np.where(template_labels == label)[0]

        temp_traces = template_traces[index]
        temp_dwt_matrix = []

        for trace in temp_traces:
            target_trace = np.array(target_trace, dtype=float)
            trace = np.array(trace, dtype=float)

            distance = dtw.distance_fast(target_trace, trace)

            temp_dwt_matrix.append(distance)

        mean_dwt = np.mean(temp_dwt_matrix)
        q5 = np.percentile(temp_dwt_matrix, 5)
        q95 = np.percentile(temp_dwt_matrix, 95)
        min_dwt = np.min(temp_dwt_matrix)

        temp_target_label[label] = {
            "mean": round(mean_dwt, 4),
            "q5": round(q5, 4),
            "q95": round(q95, 4),
            "min": round(min_dwt, 4),
            "all_matrix":temp_dwt_matrix,
            "num_ref_traces": len(temp_traces),
        }

    return temp_target_label, temp_dwt_matrix


def cluster_target_statis(target_trace, template_labels, template_traces):

    template_traces_arr = np.array(template_traces, dtype=object)

    temp_dwt_matrix = []
    for trace in template_traces_arr:
        target_trace = np.array(target_trace, dtype=float)
        trace = np.array(trace, dtype=float)

        distance = dtw.distance_fast(target_trace, trace)

        temp_dwt_matrix.append(distance)

    cluster = template_labels[np.argmin(temp_dwt_matrix)]

    return cluster, temp_dwt_matrix

