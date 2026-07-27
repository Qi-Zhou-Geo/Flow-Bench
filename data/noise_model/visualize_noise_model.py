#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-07-27T14:29:47
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion



plt.rcParams.update( {'font.size':7,
                      'font.family': "Arial",
                      'axes.formatter.limits': (-4, 6),
                      'axes.formatter.use_mathtext': True} )

def plot_Wolin2019_model(ax, color="red", plot_type="line"):

    df = pd.read_csv(f"{project_root}/data/noise_model/low‐noise-model-Wolin2019.csv", header=0)
    freq_l, psd_lnm = df.iloc[:, 0], df.iloc[:, 1]
    psd_lnm = savgol_filter(psd_lnm, window_length=100, polyorder=2)

    df = pd.read_csv(f"{project_root}/data/noise_model/high‐noise-model-Wolin2019.csv", header=0)
    freq_h, psd_hnm = df.iloc[:, 0], df.iloc[:, 1]
    psd_hnm = savgol_filter(psd_hnm, window_length=100, polyorder=2)

    # resamping the freq as 0.1 Hz
    # the two models have different frequency resolutions due to manual digitization
    f_min = max(freq_l.min(), freq_h.min())
    f_max = min(freq_l.max(), freq_h.max())
    freq_uniform = np.arange(f_min, f_max, 0.1)

    interp_l = interp1d(freq_l, psd_lnm, kind="linear", fill_value="extrapolate")
    interp_h = interp1d(freq_h, psd_hnm, kind="linear", fill_value="extrapolate")

    psd_lnm_resampled = interp_l(freq_uniform)
    psd_hnm_resampled = interp_h(freq_uniform)


    if plot_type == "line":
        ax.plot(freq_uniform, psd_lnm_resampled, color=color, lw=0.5, ls="-", zorder=1, label="Low noise model")
        ax.plot(freq_uniform, psd_hnm_resampled, color=color, lw=0.5, ls="--", zorder=1, label="High noise model")
    elif plot_type == "area":
        # interpolate high-noise model onto low-noise frequency grid
        ax.fill_between(freq_uniform, psd_lnm_resampled, psd_hnm_resampled,
                        color=color, alpha=0.5, label="High-Frequency noise model", zorder=1)
    else:
        print(f"Error! Please check the <plot_type> == {plot_type}")

    return ax

def plot_Peterson1993_model(ax, color="red", plot_type="line"):

    with np.load(f"{project_root}/data/noise_model/low-noise-model-Peterson1993.npz") as f:
        periods_l, psd_lnm = f["periods"], f["lnm"]
        # low noise model, for information on New High/Low Noise Model see [Peterson1993].

    with np.load(f"{project_root}/data/noise_model/high-noise-model-Peterson1993.npz") as f:
        periods_h, psd_hnm = f["periods"], f["hnm"]
        # high noise model, for information on New High/Low Noise Model see [Peterson1993].

    if plot_type == "line":
        ax.plot(1 / periods_l, psd_lnm, color=color, lw=1.5, ls="-", zorder=1, label="Low noise model")
        ax.plot(1 / periods_h, psd_hnm, color=color, lw=1.5, ls="--", zorder=1, label="High noise model")
    elif plot_type == "area":
        # interpolate high-noise model onto low-noise frequency grid
        # the two models have different frequency resolutions due to manual digitization
        freq_l = 1 / periods_l
        freq_h = 1 / periods_h
        psd_hnm_interp = np.interp(freq_l, freq_h, psd_hnm)

        ax.fill_between(freq_l, psd_lnm, psd_hnm_interp, color=color, alpha=0.5, label="Noise model", zorder=1)
    else:
        print(f"Error! Please check the <plot_type> == {plot_type}")

    return ax

def plot_standard_noise(ax):

    color_list = ["red", "pink", "black", "blue", "purple"]
    beta_list = [-2, -1, 0, 1, 2]

    for color, beta in zip(color_list, beta_list):
        ax.axhline(y=beta, color=color, lw=0.5, ls="--", zorder=1)
        ax.axvline(x=beta, color=color, lw=0.5, ls="--", zorder=1)