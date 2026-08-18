#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-17T21:43:02
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

from obspy import Stream, UTCDateTime

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

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
from func.seismic.plot_obspy_st import time_series_plot


def plot_sta_lta(
    # obspy stream
    st,
    sta_lta_timing,
    # STA-LTA
    sta,
    lta,
    thr_on,
    thr_off,
    # default params
    f_min,
    f_max,
    # show and save
    show_plot,
    save_plot,
    png_path,
    png_name,
):

    # (1) prepare the data
    obspy_streams = Stream()
    obspy_streams = obspy_streams + st
    obspy_streams = obspy_streams + sta_lta_timing["smooth_forward_st"]
    obspy_streams = obspy_streams + sta_lta_timing["inverse_smooth_backward_st"]

    time_markers = None
    time_markers_label = None

    stats = obspy_streams[0].stats
    starttime = stats.starttime
    sps = stats.sampling_rate

    # (2) plot it
    fig, axes = time_series_plot(
        obspy_streams=obspy_streams, time_markers=time_markers, time_markers_label=time_markers_label
    )
    y_label = ["Amplitude\n[m/s]", "STA/LTA\nForward Ratio", "STA/LTA\nBackward Ratio"]

    for idx, (ax, label) in enumerate(zip(axes, y_label)):
        ax.set_ylabel(f"{label}", fontweight="bold")

        if idx == 0:
            label = (
                f"STA={sta} s, LTA={lta} s\n"
                f"f_min={f_min} Hz, f_max={f_max} Hz\n"
                f"threshold_on={thr_on}, threshold_off={thr_off}"
            )
            ax.set_title(label=label, fontsize=7, fontweight="bold")
        else:
            ax.axhline(y=thr_on, color="red", ls="--", lw=1, alpha=0.5, zorder=5, label=f"thr_on={thr_on}")
            ax.axhline(y=thr_off, color="green", ls="-", lw=1, alpha=0.5, zorder=4, label=f"thr_off={thr_off}")
            ax.set_ylim(0, 1)

    # (3) replot the time marker
    # plot start and end time markers
    event_timing = sta_lta_timing["event_timing"]
    color_list = [f"C{i}" for i in range(len(event_timing.items()))]

    for i, (key, value) in enumerate(event_timing.items()):
        if "start" in key:
            ls = "-"
            legend_axis = 1
            marker_label = f"start: {value}"

        elif "end" in key:
            ls = "--"
            legend_axis = 2
            marker_label = f"end: {value}"

        else:
            continue

        for idx, ax in enumerate(axes):
            x = (UTCDateTime(value) - starttime) * sps  # type: ignore

            if idx == legend_axis:
                label = marker_label
            else:
                label = "_nolegend_"

            ax.axvline(x=x, color=color_list[i], lw=1, ls=ls, zorder=1, label=label)

    label = f"{stats.network}-{stats.station}-{stats.channel}-{stats.sampling_rate}"
    black_line = Line2D([0], [0], color="black", label=label)
    axes[0].legend(handles=[black_line], fontsize=6, loc="upper right")
    axes[1].legend(fontsize=6, loc="upper right")
    axes[2].legend(fontsize=6, loc="upper left")

    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0.3)

    if save_plot is True:
        png_path = Path(png_path) / png_name
        png_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"png plots will be saved at:\n{png_path}\n\n")
        plt.savefig(png_path, dpi=600, transparent=False)

    if show_plot is True:
        plt.show()

    plt.close(fig)
