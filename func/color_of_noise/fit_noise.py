#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
#from brokenaxes import brokenaxes

from scipy.stats import linregress
from scipy.stats import t as student_t  # Student's t-distribution
from scipy.stats import gaussian_kde

from obspy import read
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
from func.seismic.st2tr import stream_to_trace
from func.seismic.welch_spectrum import welch_psd
from func.toolkit.confidence_level_test import statistical_testing
from data.noise_model.visualize_noise_model import plot_Wolin2019_model, plot_standard_noise


plt.rcParams.update( {'font.size':7,
                      'font.family': "Arial",
                      'axes.formatter.limits': (-4, 6),
                      'axes.formatter.use_mathtext': True} )


def load_pre_calculated_psd(event_id, project_root):

    freq_npz_dir = f"{project_root}/data/seismic_temp/npz"
    freq_npz_file = os.listdir(freq_npz_dir)
    freq_npz_file.sort()
    if ".DS_Store" in freq_npz_file:
        freq_npz_file.remove(".DS_Store")

    with np.load(f"{freq_npz_dir}/{freq_npz_file[event_id]}", allow_pickle=True) as f:
        amp = f["freq"], f["psd"], f["psd_unit"]

    return freq, psd, psd_unit

def convert_st2psd(st):
    tr = stream_to_trace(st)
    data = tr.data
    sampling_rate = tr.stats.sampling_rate
    f_min = 1
    f_max = int(sampling_rate/2)

    freq, psd, psd_unit = welch_psd(data, sampling_rate, f_min, f_max, segment_window=10, scaling="density", unit_dB=True)

    return freq, psd, psd_unit

def find_peak_freq(freq, psd):

    peak_freq_id = np.where(psd == np.max(psd))[0]

    if len(peak_freq_id) != 1:
        print("there are multiple peak frequency!!")
        exit()
    else:
        peak_freq_id = peak_freq_id[0]

    peak_freq = freq[peak_freq_id]

    # left hand of the curve
    freq_left = freq[:peak_freq_id+1]
    psd_left = psd[:peak_freq_id+1]

    # right hand of the curve
    freq_right = freq[peak_freq_id:]
    psd_right = psd[peak_freq_id:]

    return peak_freq, freq_left, psd_left, freq_right, psd_right

def fit_color_of_noise(freq, psd, confidence_interval=0.95):
    '''
    Fit the color of noise in log-log plot

    Args:
        freq: unit by Hz,
        psd: unit by dB, PSD (unit by dB) = 10 * log10(PSD_linear)
        confidence_interval: float

    Returns:

    '''

    x = np.log10(freq)
    y = psd

    # fit the linear model by linear least-squares regression
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    r_squared = r_value ** 2


    if p_value >= 0.05:
        print(f"p_value greater than 0.05")

    # calculate 95% confidence interval on slope and intercept:
    n = len(x)
    degree_of_freedom = n - 2  # Degrees of freedom (n-2)
    alpha = 1 - confidence_interval  # significance level

    # cumulative probability up to the critical value in the right tail of the distribution
    tail = 1 - alpha / 2
    output_ci_range = student_t.ppf(tail, degree_of_freedom) # by t-distribution


    # calculate residuals and standard error of regression
    y_pred = slope * x + intercept
    residuals = y - y_pred
    s_residual = np.sqrt(np.sum(residuals ** 2) / degree_of_freedom)


    # compute confidence intervals
    slope_range = output_ci_range * std_err
    slope_CI = (slope - slope_range, slope + slope_range)

    # divide slope by 10 to recover beta
    beta = slope / 10 # because the PSD (unit by dB) = 10 * log10(PSD_linear)
    beta_CI = (slope_CI[0] / 10, slope_CI[1] / 10)

    return beta, beta_CI, intercept, s_residual, r_squared, p_value

def plot_fitting(ax, freq, psd, confidence_interval=0.95):

    colors = ["C0", "C1"]
    temp = []

    peak_freq, freq1, psd1, freq2, psd2 = find_peak_freq(freq, psd)


    for idx, (freq_temp, psd_temp) in enumerate(zip((freq1, freq2), (psd1, psd2))):

        beta, beta_CI, intercept, s_residual, r_squared, p_value = fit_color_of_noise(freq_temp, psd_temp)
        slope = 10 * beta

        # observed data
        ax.scatter(freq_temp, psd_temp, color="black", alpha=0.5, zorder=2)
        ax.plot(freq_temp, psd_temp, color="white", zorder=2)

        # fitted data
        x_log = np.log10(freq_temp)
        fitted_psd = slope * x_log + intercept
        ax.plot(freq_temp, fitted_psd, color=colors[idx], zorder=3,
                label=f"Linear least-squares regression\n"
                      f"beta={beta:.3f}, R_squared={r_squared:.3f}")

        # calculate the CI for fitting data
        n = len(freq_temp)
        degree_of_freedom = n - 2
        alpha = 1 - confidence_interval
        tail = 1 - alpha / 2
        t_val = student_t.ppf(tail, degree_of_freedom)

        x_mean = np.mean(x_log)
        sxx = np.sum((x_log - x_mean) ** 2)

        # standard error of the fitted line at each point
        se_line = s_residual * np.sqrt(1 / n + (x_log - x_mean) ** 2 / sxx)

        # confidence interval
        ci_delta = t_val * se_line
        ci_lower = fitted_psd - ci_delta
        ci_upper = fitted_psd + ci_delta

        ax.fill_between(freq_temp, ci_lower, ci_upper, color=colors[idx], alpha=0.5, zorder=4,
                        label=f"{confidence_interval} Confidence Interval")

        temp.append([beta, beta_CI, intercept, s_residual, r_squared, p_value, peak_freq])

    ax.vlines(x=peak_freq, ymin=-200, ymax=-60, zorder=1, color="green",
              label=f"Peak frequency {peak_freq:.2f} Hz")
    ax.set_xlim(1, 100)
    ax.set_ylim(-200, -60)
    ax.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.5, zorder=1)
    ax.set_xscale('log')

    handles, labels = ax.get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))
    ax.legend(unique_labels.values(), unique_labels.keys(),
              loc="upper left", fontsize=6)

    return temp


st = read(f"{project_root}/data/seismic_temp/seis/018-European-Illgraben-9J-IGB02-HHZ.mseed")
tr = st.copy()
tr.trim(UTCDateTime("2014-07-12T14:58:01"), UTCDateTime("2014-07-12T15:36:35"))
freq, psd, psd_unit = convert_st2psd(st=tr)

freq_max = 50 # Hz
index = np.where(freq>=freq_max)[0][0] + 1
freq, psd = freq[:index], psd[:index]


fig = plt.figure(figsize=(5, 5))
gs = gridspec.GridSpec(1, 1)

ax = plt.subplot(gs[0])
plot_Wolin2019_model(ax, color="#D9544D", plot_type="area")
plot_fitting(ax, freq, psd, confidence_interval=0.95)

ax.set_xlabel("Frequency [Hz]", fontweight='bold')
ax.set_ylabel("Power Spectral Density [dB]", fontweight='bold')

plt.tight_layout()
plt.savefig(f"/Users/qizhou/Desktop/fit-noise1.png", dpi=600, transparent=True)
plt.show()

