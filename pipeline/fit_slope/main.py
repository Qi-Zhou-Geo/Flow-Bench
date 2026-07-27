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
from pipeline.fit_slope.psd_slope import plot_fitting, convert_st2psd
from data.noise_model.visualize_noise_model import plot_Wolin2019_model, plot_standard_noise
from func.toolkit.multi_process_archive import dump_as_row
from func.toolkit.arial_font import add_arial_font
# add the arial_font in Glic
add_arial_font()


def set_st_path():

    # set the data path
    st_path = f"{project_root}/data/seismic_temp/seis"
    st_file_list = os.listdir(st_path)
    st_file_list = sorted(st_file_list)
    if '.DS_Store' in st_file_list:
        st_file_list.remove('.DS_Store')

    return st_file_list


def main(idx,
         st_file_list, 
         f_min, f_max):

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

    sta_s = row_idx["Start-time(UTC+0)-by-STA/LTA"]
    sta_e = row_idx["End-time(UTC+0)-by-STA/LTA"]
    # </editor-fold>


    # load the pre-processed (detrean, demean, remove sensor response) seismic data
    st_file = st_file_list[idx]
    output_name = st_file.split(".")[0]
    st = read(f"{project_root}/data/seismic_temp/seis/{st_file}")
    # do not use band pass, use the STA/LTA based time period
    st.trim(UTCDateTime(sta_s), UTCDateTime(sta_e))

    tr = st.copy()
    freq, psd, psd_unit = convert_st2psd(st=tr)

    mask = (freq >= f_min) & (freq <= f_max)
    freq_selected = freq[mask]
    psd_selected = psd[mask]

    # save the processed psd-freq.
    output_path = f"{project_root}/data/seismic_temp/psd-freq/"
    os.makedirs(output_path, exist_ok=True)
    np.savez(f"{output_path}/{output_name}.npz",
             output_name=output_name,
             freq=freq_selected,
             psd=psd_selected,
             psd_unit=psd_unit)

    # start the func.
    fig = plt.figure(figsize=(5, 5))
    gs = gridspec.GridSpec(1, 1)

    ax = plt.subplot(gs[0])
    title_text = f"Data: {sta_s} to {sta_e}, SPS={sps}"
    ax.set_title(title_text, fontsize=7, fontweight='bold')
    
    plot_Wolin2019_model(ax, color="#D9544D", plot_type="area")
    record = plot_fitting(ax, freq_selected, psd_selected, confidence_interval=0.95)
    
    ax.set_xlabel("Frequency [Hz]", fontweight='bold')
    ax.set_ylabel("Power Spectral Density [dB]", fontweight='bold')

    plt.tight_layout()
    output_dir = f"{current_dir}/plots"
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f"{output_dir}/{output_name}.png", dpi=600, transparent=True)
    # plt.show()
    plt.close(fig=fig)
    
    # dump the fited results
    output_name = f"fitted_slope.txt"
    variable_str = st_file.split(".")[0]
    # record is [beta, beta_CI[0], beta_CI[1], intercept, s_residual, r_squared, p_value, peak_freq]
    record = record
    output_dir = f"{current_dir}"
    dump_as_row(output_dir, output_name, variable_str, *record)

if __name__ == "__main__":
    # sinfo -n node[501-514] -N --Format="Nodelist,CPUsState,AllocMem,Memory,GresUsed,Gres"
    parser = argparse.ArgumentParser(description='input parameters')

    parser.add_argument("--idx", default=0, type=int)

    args = parser.parse_args()

    # start the labeling
    st_file_list = set_st_path()
    f_min, f_max = 1, 50

    main(args.idx, st_file_list, f_min, f_max)

    print(f"Done! {args.idx}")
