#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2024-03-21
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do NOT distribute this code without the author's permission

import os
import argparse
from itertools import product

import pandas as pd
import numpy as np
from scipy.signal import savgol_filter

from obspy import read, Stream, Trace, read_inventory, signal
from obspy.core import UTCDateTime # default is UTC+0 time zone

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable


# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>

# import the custom functions
from functions.color_of_noise.colored_noise import *
from functions.seismic_data_processing_obspy.welch_spectrum import welch_psd

plt.rcParams.update( {'font.size':7, 'font.family': "Arial",
                      'axes.formatter.limits': (-4, 6),
                      'axes.formatter.use_mathtext': True} )




st = read("./9S.ILL12.EHZ.2022.156_processed.mseed")
st = st[0]

# time domain
fig = plt.figure(figsize=(5.5, 4))
gs = gridspec.GridSpec(4, 1)

ax = plt.subplot(gs[3])
ax.plot(st.times("matplotlib"), st.data, color="black", zorder=2,
        label=f"{st.stats.station}-{st.stats.channel}-1-45Hz")  # Use relative time in seconds
ax.xaxis_date()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.set_xlim(st.times("matplotlib")[0], st.times("matplotlib")[-1])
ax.legend(loc="upper right", fontsize=5)


noise_type_list = ["white_noise", "red_noise", "pink_noise"]
for idx, noise_type in enumerate(noise_type_list):
    white_noise_f, white_noise_t = make_noise(noise_type, st.stats.npts, st.stats.sampling_rate)
    temp_data = white_noise_t
    tr = create_trace(temp_data, st.stats.sampling_rate, st)
    tr = tr[0]
    ax = plt.subplot(gs[idx])
    if idx == 0:
        color = "grey"
    else:
        color = noise_type.split("_")[0]
    ax.plot(tr.times("matplotlib"), tr.data, color=color, zorder=2,
            label=f"{noise_type}-{tr.stats.station}-{tr.stats.channel}-1-45Hz")  # Use relative time in seconds
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax.set_xlim(tr.times("matplotlib")[0], tr.times("matplotlib")[-1])
    ax.legend(loc="upper right", fontsize=5)
    ax.axes.xaxis.set_ticklabels([])

# for y label
fig.text(x=0, y=0.5, s="Amplitude [m/s]", weight='bold', va='center', rotation='vertical')
# for x label
fig.text(x=0.5, y=0, s=f"Time from {st.stats.starttime.strftime('%Y-%m-%d')} [UTC+0]", fontweight="bold",
         ha='center')

plt.tight_layout()
plt.subplots_adjust(hspace=0)
plt.savefig(f"./color_noise.png", dpi=600)
plt.close(fig)


def plot_noise_model(ax, noise_model="Wolin2019", color="black"):

    if noise_model == "Peterson1993":
        with np.load(f"{project_root}/plotting/fig1/noise_model/low-noise-model-Peterson1993.npz") as f:
            periods_l, psd_lnm = f["periods"], f["lnm"]
            # low noise model, for information on New High/Low Noise Model see [Peterson1993].
            ax.plot(1 / periods, psd_lnm, color=color, lw=1.5, ls="--", zorder=5, label="Low noise model")

        with np.load(f"{project_root}/plotting/fig1/noise_model/high-noise-model-Peterson1993.npz") as f:
            periods_h, psd_hnm = f["periods"], f["hnm"]
            # high noise model, for information on New High/Low Noise Model see [Peterson1993].
            ax.plot(1 / periods, psd_hnm, color=color, lw=1.5, ls="-", zorder=5, label="High noise model")

    if noise_model == "Wolin2019":
        from scipy.signal import savgol_filter

        df = pd.read_csv(f"{project_root}/plotting/fig1/noise_model/low‐noise-model-Wolin2019.csv", header=0)
        periods_l, psd_lnm = 1/df.iloc[:, 0], df.iloc[:, 1]
        psd_lnm = savgol_filter(psd_lnm, window_length=15, polyorder=2)

        df = pd.read_csv(f"{project_root}/plotting/fig1/noise_model/high‐noise-model-Wolin2019.csv", header=0)
        periods_h, psd_hnm = 1/df.iloc[:, 0], df.iloc[:, 1]
        psd_hnm = savgol_filter(psd_hnm, window_length=15, polyorder=2)

    ax.plot(1 / periods_l, psd_lnm, color=color, lw=1, ls="-", zorder=2, label="High-frequency low-noise model")
    ax.plot(1 / periods_h, psd_hnm, color=color, lw=1, ls="--", zorder=2, label=f"High-frequency high-noise model\n(Wolin and McNamara (2020)")


# ferquency domian
f_min, f_max = 1, 45
fig = plt.figure(figsize=(5, 3))
gs = gridspec.GridSpec(5, 2)
ax = plt.subplot(gs[:, 0])

noise_type_list = ["red_noise", "pink_noise", "white_noise", "blue_noise", "purple_noise"]
color_list = ["red", "pink", "black", "blue", "purple"]
beta = [-2, -1, 0, 1, 2]

for idx, noise_type in enumerate(noise_type_list):
    synthetic_data_f, synthetic_data_t = make_noise(noise_type, st.stats.npts, st.stats.sampling_rate)
    freq, psd, psd_unit = welch_psd(synthetic_data_t, st.stats.sampling_rate, f_min, f_max)

    # re scaled to psd to [-200, -80],
    # and put the first point of the "psd" as -140 dB
    minus_value = psd[0] - -140
    #label = f'{noise_type.replace("_", " ")}\n' + r'$\beta$'+ f'={beta[idx]}'
    label = f'{noise_type.split("_")[0]} ' + r'$\beta$' + f'={beta[idx]}'
    ax.plot(freq, psd - minus_value, color=color_list[idx])

    if -150 < (psd - minus_value)[-1] < -130:
        ax.text(x=10, y=(psd - minus_value)[-1] + 5, s=label, ha="left", va="center")
    else:
        ax.text(x=10, y=(psd - minus_value)[-1], s=label, ha="left", va="center")

    ax1 = plt.subplot(gs[idx*2 + 1])
    ax1.plot(synthetic_data_t, color=color_list[idx])
    ax1.set_xlim(0, synthetic_data_t.size)


    if noise_type == "white_noise":
        ax1.set_ylabel("Normalized Amplitude", fontweight="bold")

    if noise_type == "purple_noise":
        ax1.set_xlabel("Time [hour]", fontweight="bold")
        x_location = np.arange(0, synthetic_data_t.size+1, 3600*100*6)
        x_label = np.arange(0, 25, 6)
        ax1.set_xticks(x_location, x_label)
    else:
        ax1.axes.xaxis.set_ticklabels([])


ax.set_ylim(-200, -80)
ax.grid(axis='both', ls="--", lw=0.5, zorder=1)
ax.set_ylabel("PSD [dB]", fontweight="bold")
ax.set_xscale('log')
ax.set_xlabel("Frequency [Hz]", fontweight="bold")
plot_noise_model(ax)
ax.legend(loc="lower left", fontsize=6)

ax.text(x=0.1, y=-90, s="PSD(f)" + r"$\propto f^{\beta}$")


plt.tight_layout()
plt.subplots_adjust(hspace=0.1)
plt.savefig(f"./color_noise_freq.png", dpi=600, transparent=True)
plt.show()
plt.close(fig)
