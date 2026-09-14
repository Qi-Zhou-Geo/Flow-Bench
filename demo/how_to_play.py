#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-14T11:00:33
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import matplotlib.pyplot as plt
from matplotlib import gridspec

import numpy as np

from obspy import UTCDateTime

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent

sys.path.append(str(project_root))
# endregion

# import the custom functions
from func.flow_bench.FlowBench import FlowBench
from func.seismic.plot_obspy_st import psd_plot

# (1) Load the one debris flow event
version = "v2dot1dot5"
fb = FlowBench(version=version)
# load the meta
seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
event_meta = fb.get_metadata(meta_type="event", print_meta=False)
# print all the event by
# print(seis_meta)

# request one evnet
event_id = 14
st_raw, st_cooked = fb.request_one_seis_event(event_id=event_id)
st_raw.plot()  # type: ignore
st_cooked.plot()  # x is UTC+0 time, y is amplitude (unit by m/s)


# (2) print the metadata information
print(st_cooked[0].stats)


# (3) Find the time when the amp is maximum,
# we can assume this time stamps conspros the shortest "event to statrion"
seis_data = np.array(st_cooked[0].data)
amp_max_t = UTCDateTime(st_cooked[0].stats.starttime) + np.argmax(np.abs(seis_data)) / st_cooked[0].stats.sampling_rate
print(amp_max_t)


# (4) plot the PSD
fig = plt.figure(figsize=(6, 4))
gs = gridspec.GridSpec(3, 1, height_ratios=[10, 0.01, 1])
ax = plt.subplot(gs[0])
cbar_ax = plt.subplot(gs[2])
ax, data_sps = psd_plot(
    fig=fig,
    ax=ax,
    cbar_ax=cbar_ax,
    st=st_cooked.copy(),
    fix_colorbar=True,
    per_lap=0.5,
    wlen=60,
    x_interval=1,
)
ax.set_ylim(1, 25)
ax.set_xlabel("UTC+0 Time", fontweight="bold")

plt.tight_layout()
png_path = Path(current_dir) / "psd_2014-07-12.png"
plt.savefig(png_path, dpi=600)
plt.show()
plt.close(fig)
