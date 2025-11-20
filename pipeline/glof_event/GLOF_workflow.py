#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou and Sibashish Dash, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import yaml

import argparse

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MultipleLocator

from scipy.stats import linregress
from scipy.stats import t as student_t  # Student's t-distribution
from scipy.stats import gaussian_kde

from obspy import Stream, Trace, read
from obspy.core import UTCDateTime  # default is UTC+0 time zone

from scipy.signal import hilbert

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path

current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys

sys.path.append(str(project_root))
# </editor-fold>

# import the custom functions

plt.rcParams.update({'font.size': 7,
                     'font.family': "Arial",
                     'axes.formatter.limits': (-4, 6),
                     'axes.formatter.use_mathtext': True})


# <editor-fold desc="Step 1-1">
## ------------------------ Step 1-1 ------------------------ ##
from pipeline.define_s_e.define_event_timing import find_st_timing


seismic_sta_list = ["NEP08", "NEP07", "NEP06", "NEP10", "NEP05", "NEP04"]
archived_data = "data/seismic_temp/seis"
data_start, data_end = "2016-07-05T14:00:00", "2016-07-05T19:00:00"

window_size, window_ovelap, denoising_method = 1, 0, "RMS"
short_window, long_window, ratio_on, ratio_off = 180, 1800, 3, 2
f_min, f_max = 5, 25

for idx, sta in enumerate(seismic_sta_list):

    if sta == "NEP08":
        idy = "085"
    else:
        idy = str(idx+139).zfill(3)

    st = read(f"{project_root}/{archived_data}/{idy}-Asian-Bothekoshi-XN-{sta}-HHZ.mseed")

    st.trim(UTCDateTime(data_start), UTCDateTime(data_end))
    st.filter("bandpass", freqmin=f_min, freqmax=f_max)
    st.detrend('linear')
    st.detrend('demean')

    output_name = f"{idy}-Asian-Bothekoshi-XN-{sta}-HHZ"

    find_st_timing(st, window_size, window_ovelap, denoising_method,
                   short_window, long_window, ratio_on, ratio_off,
                   f_min, f_max,
                   output_name)

    print(f"Done: {sta}")

# </editor-fold>


## ------------------------ Step 1-2 ------------------------ ##
# manually selected the sta_s, sta_e
sta_time = {"NEP08": "2016-07-05T15:16:27_2016-07-05T17:07:48",
            "NEP07": "2016-07-05T15:23:00_2016-07-05T17:15:00",
            "NEP06": "2016-07-05T15:23:00_2016-07-05T17:16:00",
            "NEP10": "2016-07-05T15:23:00_2016-07-05T17:32:00",
            "NEP05": "2016-07-05T15:26:00_2016-07-05T16:02:00",
            "NEP04": "2016-07-05T15:25:00_2016-07-05T16:03:00"}

# <editor-fold desc="Step 2-1">
## ------------------------ Step 2-1 ------------------------ ##
from pipeline.fit_slope.psd_slope import plot_fitting, convert_st2psd
from data.noise_model.visualize_noise_model import plot_Wolin2019_model, plot_standard_noise
from functions.toolkit.multi_process_archive import dump_as_row

f_min, f_max = 1, 50
for idx, sta in enumerate(seismic_sta_list):

    if sta == "NEP08":
        idy = "085"
    else:
        idy = str(idx + 139).zfill(3)

    st = read(f"{project_root}/{archived_data}/{idy}-Asian-Bothekoshi-XN-{sta}-HHZ.mseed")

    sta_s, sta_e = sta_time.get(sta).split("_")

    # do not use band pass, use the STA/LTA based time period
    st.trim(UTCDateTime(sta_s), UTCDateTime(sta_e))

    tr = st.copy()
    freq, psd, psd_unit = convert_st2psd(st=tr)


    mask = (freq >= f_min) & (freq <= f_max)
    freq_selected = freq[mask]
    psd_selected = psd[mask]


    # start the func.
    output_name = f"{idy}-Asian-Bothekoshi-XN-{sta}-HHZ_beta"
    sps = st[0].stats.sampling_rate

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
    output_name = f"GLOF_fitted_slope.txt"
    variable_str = sta
    # record is [beta, beta_CI[0], beta_CI[1], intercept, s_residual, r_squared, p_value, peak_freq]
    record = record
    output_dir = f"{current_dir}"
    dump_as_row(output_dir, output_name, variable_str, *record)

# </editor-fold>


# <editor-fold desc="Step 3-1">
## ------------------------ Step 3-1 ------------------------ ##
import pickle
from functions.seismic.signal_denoising import st_denoising
from functions.seismic.generate_seismic_trace import create_trace
from functions.seismic.st2tr import stream_to_trace
from functions.dynamic_time_warping.dwt_warping import cluster_target, cluster_target_statis
from functions.dynamic_time_warping.dwt_warping import min_max_normalize

def plot_DWT_example(s1, s2, note1, note2):

    from dtaidistance import dtw
    from dtaidistance import dtw_visualisation as dtwvis

    fig = plt.figure(figsize=(6, 4))
    gs = gridspec.GridSpec(2, 1)
    ax1 = plt.subplot(gs[0])
    ax2 = plt.subplot(gs[1])

    distance = dtw.distance_fast(s1, s2)
    ax1.set_title(f"(a) {note1}", fontweight='bold', loc='left', fontsize=7)
    ax2.set_title(f"(b) {note2}", fontweight='bold', loc='left', fontsize=7)

    path = dtw.warping_path(s1, s2)
    dtwvis.plot_warping(s1, s2, path, fig=fig, axs=[ax1, ax2],
                        series_line_options={'linewidth': 1, 'color': 'black', 'alpha': 1},
                        warping_line_options={'linewidth': 0.1, 'color': 'C0', 'alpha': 0.2})

    ax1.set_xlim(0, len(s1))
    ax2.set_xlim(0, len(s2))
    ax1.xaxis.set_major_locator(MultipleLocator(30))
    ax2.xaxis.set_major_locator(MultipleLocator(30))
    ax1.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.5, zorder=1)
    ax2.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.5, zorder=1)
    ax1.set_ylabel("Normalized Amplitude", fontweight='bold')
    ax2.set_ylabel("Normalized Amplitude", fontweight='bold')
    ax1.set_xlabel("Time [minute]", fontweight='bold')
    ax2.set_xlabel("Time [minute]", fontweight='bold')

    x_location = np.arange(0, ax1.get_xlim()[1], 120)
    x_ticks = [int(i / 6) for i in x_location]
    ax1.set_xticks(x_location, x_ticks)

    x_location = np.arange(0, ax2.get_xlim()[1], 120)
    x_ticks = [int(i / 6) for i in x_location]
    ax2.set_xticks(x_location, x_ticks)

    fig.suptitle(f'Dynamic Time Warping (DTW) Distance = {distance: .3f}', fontsize=7, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{current_dir}/glof-df-dwt-example-with-line.png", dpi=600, transparent=True)
    plt.show()


# smooth the GLOF trace
f_min, f_max = 1, 50
window_size, window_overlap, denoising_method = 10, 0, "RMS"

nep_trace_list = []
for idx, sta in enumerate(seismic_sta_list):

    if sta == "NEP08":
        idy = "085"
    else:
        idy = str(idx + 139).zfill(3)

    st = read(f"{project_root}/{archived_data}/{idy}-Asian-Bothekoshi-XN-{sta}-HHZ.mseed")

    st.trim(UTCDateTime(data_start), UTCDateTime(data_end))
    print(sta, data_start, data_end)
    st.filter("bandpass", freqmin=f_min, freqmax=f_max)
    st.detrend('linear')
    st.detrend('demean')

    t_value, x_value, low_sampling_rate, denoised_st = st_denoising(st, window_size, window_overlap, denoising_method)
    tr = create_trace(data=x_value, start_time=t_value[0], data_sampling_rate=low_sampling_rate, ref_st=st)
    tr = stream_to_trace(st=tr)

    amp = tr.data
    amp = min_max_normalize(amp)
    nep_trace_list.append(amp)

# load the ILL traces
cached_file = Path(f"{project_root}/pipeline/cal_dwt_matrix/traces_list.pkl")
event_seperator = 66

with open(cached_file, "rb") as f:
    data = pickle.load(f)
    traces_list = data["traces_list"]
    unique_id_list = data["unique_id_list"]

ILL_traces = traces_list[:event_seperator]
unique_id_list_ILL = unique_id_list[:event_seperator]


# load the label and traces
obj_trace = "ILL_traces"
temp = np.load(f"{project_root}/pipeline/cal_dwt_matrix/traces_amp_{obj_trace}.npz", allow_pickle=True)
template_traces = temp["traces_amp"]
template_labels = temp["traces_cluster_labels"]



# only find the cluster
cluster_labels_nonILL = []
cluster_labels_nonILL_stats = []
nonILL_fitted_all_dwt_d = []
for idx, target_trace in enumerate(nep_trace_list):

    temp_target_label, temp_dwt_matrix = cluster_target(target_trace, template_labels, template_traces)

    # find the best label based the min DWT
    best_cluster = min(
        temp_target_label,
        key=lambda k: temp_target_label[k]["min"]
        # key=lambda k: temp_target_label[k]["mean"]
    )

    # find the best stats
    best_stats = temp_target_label[best_cluster]
    mean_dwt = best_stats['mean']
    q5, q95 = best_stats['q5'], best_stats['q95']
    min_dwt = best_stats['min']
    num_ref_traces = best_stats['num_ref_traces']

    cluster_labels_nonILL.append(best_cluster)
    cluster_labels_nonILL_stats.append(best_stats)
    nonILL_fitted_all_dwt_d.append(temp_dwt_matrix )

    print(f"{idx}, {seismic_sta_list[idx]}, Cluster: {best_cluster}, Stats: {q5}, {q95}, {mean_dwt}, {min_dwt}")


# only find the statis
cluster_labels_nonILL = []
nonILL_fitted_all_dwt_d = []
for idx, target_trace in enumerate(nep_trace_list):

    best_cluster, temp_dwt_matrix = cluster_target_statis(target_trace, template_labels, template_traces)

    cluster_labels_nonILL.append(best_cluster)
    nonILL_fitted_all_dwt_d.append(temp_dwt_matrix)

# do the statis, find the most similarity DF for GLOF
for idx, sta in enumerate(seismic_sta_list):
    print(f"{sta}, min, median, max"
          f"{np.min(nonILL_fitted_all_dwt_d[idx]) :.2f}, "
          f"{np.median(nonILL_fitted_all_dwt_d[idx]) :.2f}, "
          f"{np.max(nonILL_fitted_all_dwt_d[idx]) :.2f}, "
          f"the np.argmin(nonILL_fitted_all_dwt_d[idx]) = {np.argmin(nonILL_fitted_all_dwt_d[idx])}")

s1 = nep_trace_list[0]
note1 = sta_time.get("NEP08").split("_")[0]
note1 = f"GLOF recorded at station NEP08, time from {note1}"
s2 = template_traces[44]
note2 = "2019-07-02T22:09:25"
note2 = f"DF recorded at station NEP08, time from {note2}"
plot_DWT_example(s1, s2, note1, note2)
# </editor-fold>


# # <editor-fold desc="Step 4-1">
# ## ------------------------ Step 4-1 ------------------------ ##
from functions.color_of_noise.plot_psd_slope_func import plot_contour
from functions.color_of_noise.plot_psd_slope_func import plot_ILL_noise_model

def plot_GLOG_slope(event_seperator=66, clip_min=0, clip_max=10):

    fig = plt.figure(figsize=(6, 3))
    gs = gridspec.GridSpec(1, 2)
    ax = plt.subplot(gs[1])
    ax.set_title("(b)", fontsize=7, loc='left')

    df2 = pd.read_csv(f"{project_root}/pipeline/fit_slope/fitted_slope.txt", header=None)
    df2 = np.array(df2)
    slope_left = df2[:, 1].astype(float)
    slope_left_CI1 = df2[:, 2].astype(float)
    slope_left_CI2 = df2[:, 3].astype(float)

    slope_right = df2[:, 9].astype(float)
    slope_right_CI1 = df2[:, 10].astype(float)
    slope_right_CI2 = df2[:, 11].astype(float)

    _, x_start, x_end, y_start, y_end, label_temp = plot_contour(ax=ax,
                                                                 slope1=slope_left[:event_seperator],
                                                                 slope2=slope_right[:event_seperator],
                                                                 plot_legend=False)

    df2 = pd.read_csv(f"{current_dir}/GLOF_fitted_slope.txt", header=None)
    df2 = np.array(df2)
    slope_left = df2[:, 1].astype(float)
    slope_left = np.clip(slope_left, clip_min, clip_max)
    slope_left_CI1 = df2[:, 2].astype(float)
    slope_left_CI2 = df2[:, 3].astype(float)

    slope_right = df2[:, 9].astype(float)
    slope_right = np.clip(slope_right, -1 * clip_max, clip_min)
    slope_right_CI1 = df2[:, 10].astype(float)
    slope_right_CI2 = df2[:, 11].astype(float)

    marker = ["^", "o", "s", "D", "v", "*"]
    for idx in range(len(df2)):

        xerr = slope_left_CI2[idx] - slope_left_CI1[idx]
        yerr = slope_right_CI2[idx] - slope_right_CI1[idx]

        if np.isnan(slope_left[idx]):
            s1 = clip_max
        else:
            s1 = slope_left[idx]

        if np.isnan(slope_right[idx]):
            s2 = clip_max
        else:
            s2 = slope_right[idx]

        if np.isnan(xerr):
            xerr = clip_max

        if np.isnan(yerr):
            yerr = clip_max

        label = df2[idx, 0]
        ax.errorbar(s1, s2,
                    xerr=xerr, yerr=yerr,
                    color=f"C{idx+3}",
                    label=f"{label}, Peak freq.: {df2[idx, -1]} Hz",
                    marker=marker[idx],
                    alpha=0.5)

    delta = 0.5
    ax.set_xlim(clip_min - delta, clip_max + delta)
    ax.set_ylim(-1 * clip_max - delta, clip_min + delta)
    ax.legend(fontsize=6, loc="lower right", ncol=1)

    ax.grid(ls="--", color="grey", alpha=0.5, zorder=1)
    ax.set_ylabel("Slope from Peak Frequency to 45 Hz", weight='bold')
    ax.set_xlabel("Slope from 1 Hz to Peak Frequency", weight='bold')


    ax = plt.subplot(gs[0])
    ax.set_title("(a)", fontsize=7, loc='left')

    f_min, f_max = 1, 50
    for idx, sta in enumerate(seismic_sta_list):

        if sta == "NEP08":
            idy = "085"
        else:
            idy = str(idx + 139).zfill(3)

        st = read(f"{project_root}/{archived_data}/{idy}-Asian-Bothekoshi-XN-{sta}-HHZ.mseed")

        sta_s, sta_e = sta_time.get(sta).split("_")

        # do not use band pass, use the STA/LTA based time period
        st.trim(UTCDateTime(sta_s), UTCDateTime(sta_e))

        tr = st.copy()
        freq, psd, psd_unit = convert_st2psd(st=tr)
        ax.plot(freq, psd, label=f"{sta}", zorder=5, color=f"C{idx+3}")
        ax.set_xscale('log')

    ax.legend(fontsize=6, loc="lower right", ncol=2)
    plot_Wolin2019_model(ax, color="black", plot_type="line")
    plot_ILL_noise_model(ax)
    ax.grid(ls="--", color="grey", alpha=0.5, zorder=1)

    ax.set_xlim(f_min, f_max)
    ax.set_ylim(-200, -50)
    ax.set_xlabel("Frequency [Hz]", fontweight='bold')
    ax.set_ylabel("Power Spectral Density [dB]", fontweight='bold')


    plt.tight_layout()
    plt.savefig(f"{current_dir}/glof-slope.png", dpi=600, transparent=True)
    plt.show()

plot_GLOG_slope()


# # </editor-fold>