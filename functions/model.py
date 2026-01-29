#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2026-01-14
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import argparse

import yaml

import numpy as np
import pandas as pd

from tqdm import tqdm

from obspy import UTCDateTime, read, Stream

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MultipleLocator

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent

# using ".parent" on "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>

# import the custom functions
from functions.seismic.st2tr import stream_to_trace
# STA/LTA
from functions.seismic.signal_denoising import st_denoising
from functions.labeling_debris_flow.signal_sta_lta import sta_lta_timing
from functions.seismic.plot_obspy_st import time_series_plot
# Color of Noise
from pipeline.fit_slope.psd_slope import convert_st2psd
from pipeline.fit_slope.psd_slope import plot_fitting, find_peak_freq
#DWT
from functions.seismic.generate_seismic_trace import create_trace
from functions.dynamic_time_warping.dwt_warping import min_max_normalize
from functions.dynamic_time_warping.dwt_warping import cluster_target, cluster_target_statis

class FlowBench:

    def __init__(self, model_version, output_path,
                 sub_window_size=60, window_overlap=0):

        # model params
        self.model_version = model_version

        # data segement
        self.sub_window_size = sub_window_size # unit by second
        self.window_overlap = window_overlap # # unit by ratio, 0-> none overlap, 1-> fully overlap

        # results I/O
        self.output_path = output_path
        os.makedirs(self.output_path, exist_ok=True)
        self.output_name = None

        #
        self.sta_timing = None
        self.psd_f = None


    def load_ILL_traces(self, print_log=True):

        # load the Illgraben traces
        obj_trace = "ILL_traces"
        obj_trace_path = f"{project_root}/pipeline/cal_dwt_matrix/traces_amp_{obj_trace}.npz"
        temp = np.load(obj_trace_path, allow_pickle=True)
        template_labels = temp["traces_cluster_labels"]
        template_traces = temp["traces_amp"]

        self.template_traces = template_traces
        self.template_labels = template_labels

        if print_log is True:
            print(f"Load {obj_trace} from:\n{obj_trace_path}")

        return template_labels, template_traces
    
    def load_ILL_metadata(self, event_idx):
        # event from 0

        # <editor-fold desc="prepare data">
        default_data_path = f"{project_root}/config/data_path.yaml"
        with open(default_data_path, "r") as f:
            config = yaml.safe_load(f)
            sac_path = config[f"glic_sac_dir"]
            event_catalog_version = config[f"event_catalog_version"]

        file_path = f"{project_root}/data/event_catalog/{event_catalog_version}"
        df = pd.read_csv(f"{file_path}", header=0)

        row_idx = df.loc[event_idx]  # select row_idx
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

        ILL_reference_event = {"event_catalog_version": event_catalog_version,
                               "event_idx": event_idx + 1,  # the event is from 0 in df, 1 in catalog
                               "sta_s": sta_s, "sta_e": sta_e}

        return ILL_reference_event

    def process_st(self, st, f_min, f_max, event_start=None, event_end=None):

        temp_st = st.copy()
        # seismic data and output_name
        temp_st = stream_to_trace(temp_st) # convert to trace
        temp_st.filter("bandpass", freqmin=f_min, freqmax=f_max)
        temp_st.detrend('linear')
        temp_st.detrend('demean')

        nyq_freq = int(temp_st.stats.sampling_rate / 2)

        if event_start is None or event_end is None:
            pass
        else:
            temp_st.trim(UTCDateTime(event_start), UTCDateTime(event_end))

        return temp_st, nyq_freq


    def define_event_timing(self, st,
                            window_size=1, window_overlap=0,
                            denoising_method="RMS",
                            short_window=180, long_window=1800, ratio_on=3, ratio_off=2,
                            f_min=5, f_max=25):

        tr, nyq_freq = self.process_st(st, f_min, f_max)
        output_name = (f"{tr.stats.network}-{tr.stats.station}-{tr.stats.channel}"
                       f"-{window_size}-{window_overlap}-{denoising_method}-"
                       f"{short_window}s-{long_window}s-{ratio_on}-{ratio_off}")
        self.output_name = output_name
        # double-check the params
        if window_size is None:
            w_s = self.sub_window_size
        else:
            w_s = window_size

        if window_overlap is None:
            w_o = self.window_overlap
        else:
            w_o = window_overlap

        # denoise the seismic trace using an RMS sliding window
        t_value, x_value, low_sampling_rate, denoised_st = st_denoising(tr, w_s, w_o, denoising_method)

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
            print(f"Event Start Time: {i}")

        for i in time_off:
            time_markers.append(i)
            time_markers_label.append(f"off_{i}")
            print(f"Event End Time: {i}\n")


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
        plt.savefig(f"{self.output_path}/{output_name}_{self.model_version}.png", dpi=600, transparent=False)
        plt.close(fig)

    def freq_domain(self, st,
                    event_start, event_end,
                    f_min=1, f_max=50,
                    show_plot=False):

        tr, nyq_freq = self.process_st(st, f_min, f_max, event_start, event_end)
        freq, psd, psd_unit = convert_st2psd(st=tr)
        
        f_max = min(f_max, nyq_freq)
        mask = (freq >= f_min) & (freq <= f_max)
        freq_selected = freq[mask]
        psd_selected = psd[mask]
        peak_freq, freq1, psd1, freq2, psd2 = find_peak_freq(freq_selected, psd_selected)


        # calculate and plot
        fig = plt.figure(figsize=(5, 5))
        gs = gridspec.GridSpec(1, 1)
        ax = plt.subplot(gs[0])
        record = plot_fitting(ax, freq_selected, psd_selected, confidence_interval=0.95)
        if show_plot is True:
            ax.set_xlabel("Frequency [Hz]", fontweight='bold')
            ax.set_ylabel("Power Spectral Density [dB]", fontweight='bold')

            plt.show()
        plt.close(fig)

        # for print
        params_name = ["beta", "beta_95%CI_lower", "beta_95%CI_upper",
                       "intercept", "s_residual", "r_squared", "p_value", "peak_freq"]
        fit_left = record[:8]
        fit_right = record[8:]
        df = pd.DataFrame({
            "parameter": params_name,
            f"Fitting from {f_min :.2f} to Peak Frequency {peak_freq :.2f} Hz": fit_left,
            f"Fitting from Peak Frequency {peak_freq :.2f} to {f_max} Hz": fit_right
        })

        freq_results = (f"Freq. Domain:\n"
                        f"{df.to_string(index=False, float_format='%.3g')}")
        print(freq_results)

        self.psd_f = {"freq": freq_selected,
                      "psd": psd_selected,
                      "peak_freq": peak_freq,
                      "fitted_beta": df}

    def time_domain(self, st,
                    event_start, event_end,
                    window_size=10, window_overlap=0,
                    denoising_method="RMS",
                    f_min=1, f_max=50):

        tr, nyq_freq = self.process_st(st, f_min, f_max, event_start, event_end)

        if window_size is None:
            w_s = self.sub_window_size
        else:
            w_s = window_size

        if window_overlap is None:
            w_o = self.window_overlap
        else:
            w_o = window_overlap

        t_value, x_value, low_sampling_rate, denoised_st = st_denoising(tr, w_s, w_o, denoising_method)
        tr = create_trace(data=x_value, start_time=t_value[0], data_sampling_rate=low_sampling_rate, ref_st=st)
        tr = stream_to_trace(st=tr)

        amp = tr.data
        target_trace = min_max_normalize(amp)
        template_labels, template_traces = self.load_ILL_traces(print_log=True)

        # calculate the DWT distance matrix
        best_cluster, dwt_matrix = cluster_target_statis(target_trace, template_labels, template_traces)
        greatest_similarity_id = np.argmin(dwt_matrix)
        time_results = (f"Time Domain:\n"
                        f"{tr.stats.station}, min, median, max, "
                        f"{np.min(dwt_matrix) :.2f}, "
                        f"{np.median(dwt_matrix) :.2f}, "
                        f"{np.max(dwt_matrix) :.2f}, "
                        f"the np.argmin(dwt_matrix) = {greatest_similarity_id}")

        print(time_results)
        
        self.ILL_reference_event = self.load_ILL_metadata(event_idx=greatest_similarity_id)

        self.dwt_results = {"target_trace":target_trace,
                            "similar_DF":template_traces[greatest_similarity_id],
                            "min_DWT":np.min(dwt_matrix),
                            "median_DWT":np.median(dwt_matrix),
                            "max_DWT":np.max(dwt_matrix),
                            "target_event_start":event_start,
                            "target_event_end":event_end}


    def plot(self):

        from functions.color_of_noise.plot_psd_slope_func import plot_contour

        from functions.color_of_noise.plot_psd_slope_func import plot_ILL_noise_model
        from data.noise_model.visualize_noise_model import plot_Wolin2019_model

        from dtaidistance import dtw
        from dtaidistance import dtw_visualisation as dtwvis

        fig = plt.figure(figsize=(6, 7))
        gs = gridspec.GridSpec(3, 2, height_ratios=[2, 1, 1])

        # PSD-Freq.
        ax = plt.subplot(gs[0])
        plot_fitting(ax, self.psd_f["freq"], self.psd_f["psd"], confidence_interval=0.95)
        plot_ILL_noise_model(ax, request_catchment="Illgraben")
        plot_Wolin2019_model(ax, color="black", plot_type="line")

        ax.set_title(f"(a)", fontweight='bold', loc='left', fontsize=7)
        ax.set_xlabel("Frequency [Hz]", fontweight='bold')
        ax.set_ylabel("Power Spectral Density [dB]", fontweight='bold')



        # contour line
        ax = plt.subplot(gs[1])
        s1 = self.psd_f["fitted_beta"].iloc[0, 1]
        xerr = self.psd_f["fitted_beta"].iloc[2, 1] - self.psd_f["fitted_beta"].iloc[1, 1]
        s2 = self.psd_f["fitted_beta"].iloc[0, 2]
        yerr = self.psd_f["fitted_beta"].iloc[2, 2] - self.psd_f["fitted_beta"].iloc[1, 2]

        ax.errorbar(s1, s2,
                    xerr=xerr, yerr=yerr,
                    color=f"red",
                    label=f"Peak freq.: {self.psd_f['fitted_beta'].iloc[7, 1] :.2f} Hz",
                    marker="o",
                    alpha=0.5)


        df2 = pd.read_csv(f"{project_root}/pipeline/fit_slope/fitted_slope.txt", header=None)
        df2 = np.array(df2)
        slope_left = df2[:, 1].astype(float)
        slope_right = df2[:, 9].astype(float)
        event_seperator = 66
        _, x_start, x_end, y_start, y_end, label_temp = plot_contour(ax=ax,
                                                                     slope1=slope_left[:event_seperator],
                                                                     slope2=slope_right[:event_seperator],
                                                                     plot_legend=True)

        ax.set_title(f"(b)", fontweight='bold', loc='left', fontsize=7)
        ax.grid(ls="--", color="grey", alpha=0.5, zorder=1)
        ax.set_ylabel("Slope from Peak Frequency to 45 Hz", weight='bold')
        ax.set_xlabel("Slope from 1 Hz to Peak Frequency", weight='bold')
        delta = 0.5
        clip_min = 0
        clip_max = 10
        ax.set_xlim(clip_min - delta, clip_max + delta)
        ax.set_ylim(-1 * clip_max - delta, clip_min + delta)

        # DWT
        ax1 = plt.subplot(gs[1, :])
        ax2 = plt.subplot(gs[2, :])

        s1 = self.dwt_results["target_trace"]
        s2 = self.dwt_results["similar_DF"]
        distance = dtw.distance_fast(s1, s2)

        ax1.set_title(f"(c) Target Trace", fontweight='bold', loc='left', fontsize=7)
        ax2.set_title(f"(d) Reference Trace", fontweight='bold', loc='left', fontsize=7)

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
        ax1.set_xlabel(f"Time from {self.dwt_results['target_event_start']} [minute]", fontweight='bold')
        ax2.set_xlabel(f"Time from {self.ILL_reference_event['sta_s']} [minute]", fontweight='bold')

        matrix = (
            f" Event Catalog Version: {self.ILL_reference_event['event_catalog_version']}\n"
            f" Most Similar DF {self.ILL_reference_event['event_idx']}: {self.ILL_reference_event['sta_s']}\n"
            f" DWT Distance: {distance:.3f}\n"
            f" Statistics Min: {self.dwt_results['min_DWT']:.2f}\n"
            f" Statistics Median: {self.dwt_results['median_DWT']:.2f}\n"
            f" Statistics Max: {self.dwt_results['max_DWT']:.2f}"
        )
        ax1.text(0, 1, matrix, fontsize=6, va="top")


        x_location = np.arange(0, ax1.get_xlim()[1], 120)
        x_ticks = [int(i / 6) for i in x_location]
        ax1.set_xticks(x_location, x_ticks)

        x_location = np.arange(0, ax2.get_xlim()[1], 120)
        x_ticks = [int(i / 6) for i in x_location]
        ax2.set_xticks(x_location, x_ticks)

        plt.tight_layout()
        plt.savefig(f"{self.output_path}/Summary_{self.output_name}_{self.model_version}.png", dpi=600, transparent=True)
        print(f"{self.output_path}/Summary_{self.output_name}_{self.model_version}.png")
        plt.show()
