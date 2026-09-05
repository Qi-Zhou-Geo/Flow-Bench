#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-05T14:07:21
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import matplotlib.pyplot as plt
from matplotlib import gridspec

from obspy import UTCDateTime, read

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


from func.seismic.plot_obspy_st import psd_plot


event_id = 122
seis_cat = "Shasta"
starttime = UTCDateTime("2022-07-10T20:00:00")

cache_dir = Path(project_root) / f"data/cache/{event_id:03d}_{seis_cat}_cooked_all.mseed"
st_cooked_all = read(cache_dir)

num_st = len(st_cooked_all)
half_st = int(num_st / 2)
rest_st = num_st - half_st

# plot the psd
fig = plt.figure(figsize=(6, 9))
gs = gridspec.GridSpec(half_st + 1, 1, height_ratios=[1] + [10] * half_st)

for idx, st_cooked in enumerate(st_cooked_all[:half_st]):
    if idx == 0:
        cbar_ax = plt.subplot(gs[idx])
    else:
        cbar_ax = None

    ax = plt.subplot(gs[idx + 1])
    ax, data_sps = psd_plot(
        fig,
        ax,
        cbar_ax,
        st=st_cooked,
        fix_colorbar=True,
        per_lap=0.5,
        wlen=60,
        x_interval=2,
    )

    ax.set_title(label=f"{st_cooked.stats.network}-{st_cooked.stats.station}-{st_cooked.stats.channel}", loc="left")
    ax.set_ylim(1, 25)
    ax.set_yticks([1, 15, 25], [1, 15, 25])

png_name = f"pipeline/find_best_data/{seis_cat}_{starttime.julday:03d}/psd1.png"
png_path = Path(project_root) / png_name
png_path.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(png_path, dpi=600)
plt.close(fig)


# plot the psd
fig = plt.figure(figsize=(6, 9))
gs = gridspec.GridSpec(rest_st + 1, 1, height_ratios=[1] + [10] * rest_st)

for idx, st_cooked in enumerate(st_cooked_all[half_st:]):
    if idx == 0:
        cbar_ax = plt.subplot(gs[idx])
    else:
        cbar_ax = None

    ax = plt.subplot(gs[idx + 1])
    ax, data_sps = psd_plot(
        fig,
        ax,
        cbar_ax,
        st=st_cooked,
        fix_colorbar=True,
        per_lap=0.5,
        wlen=60,
        x_interval=2,
    )

    ax.set_title(label=f"{st_cooked.stats.network}-{st_cooked.stats.station}-{st_cooked.stats.channel}", loc="left")
    ax.set_ylim(1, 25)
    ax.set_yticks([1, 15, 25], [1, 15, 25])

png_name = f"pipeline/find_best_data/{seis_cat}_{starttime.julday:03d}/psd2.png"
png_path = Path(project_root) / png_name
png_path.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(png_path, dpi=600)
plt.close(fig)


event_id = 103
seis_cat = "Hood"
starttime = UTCDateTime("2015-08-19T19:00:00")


cache_dir = Path(project_root) / f"data/cache/{event_id:03d}_{seis_cat}_cooked_all.mseed"
st_cooked_all = read(cache_dir)

num_st = len(st_cooked_all)

# plot the psd
fig = plt.figure(figsize=(6, 9))
gs = gridspec.GridSpec(num_st + 1, 1, height_ratios=[1] + [10] * num_st)

for idx, st_cooked in enumerate(st_cooked_all):
    if idx == 0:
        cbar_ax = plt.subplot(gs[idx])
    else:
        cbar_ax = None

    ax = plt.subplot(gs[idx + 1])
    ax, data_sps = psd_plot(
        fig,
        ax,
        cbar_ax,
        st=st_cooked,
        fix_colorbar=True,
        per_lap=0.5,
        wlen=60,
        x_interval=2,
    )

    ax.set_title(label=f"{st_cooked.stats.network}-{st_cooked.stats.station}-{st_cooked.stats.channel}", loc="left")
    ax.set_ylim(1, 25)
    ax.set_yticks([1, 15, 25], [1, 15, 25])

png_name = f"pipeline/find_best_data/{seis_cat}_{starttime.julday:03d}/psd.png"
png_path = Path(project_root) / png_name
png_path.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(png_path, dpi=600)
plt.close(fig)
