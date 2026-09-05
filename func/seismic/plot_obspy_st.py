#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-05T11:55:19
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
import pandas as pd

from obspy import Stream, Trace
from obspy.core import UTCDateTime  # default is UTC+0 time zone

import matplotlib.pyplot as plt
from matplotlib import gridspec

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


plt.rcParams.update(
    {
        "font.size": 7,
        "legend.fontsize": 6,
        "axes.formatter.limits": (-3, 6),
        "axes.formatter.use_mathtext": True,
    }
)


def rewrite_x_ticks(ax, data_start, data_end, data_sps, x_interval=1):
    """
    Re write the x/time ticks

    Args:
        ax:
        data_start:
        data_end:
        data_sps:
        x_interval: for PSD, levea it as 1, for waveform or other, set as SPS

    Returns:

    """
    start = UTCDateTime(data_start).timestamp
    end = UTCDateTime(data_end).timestamp

    x_location = np.arange(start, end + 1, 3600 * x_interval)
    x_ticks = []
    for j, k in enumerate(x_location):
        if j == 0:
            fmt = "%Y-%m-%d\n%H:%M:%S"
        else:
            fmt = "%H:%M"
        x_ticks.append(UTCDateTime(int(k)).strftime(fmt))

    x_location = (x_location - start) * data_sps

    ax.set_xticks(x_location, x_ticks)


def psd_plot(fig, ax, cbar_ax, st, fix_colorbar=True, per_lap=0.5, wlen=60, x_interval=1):

    st = stream_to_trace(st)
    st.spectrogram(per_lap=per_lap, wlen=wlen, log=False, dbscale=True, mult=True, title="", axes=ax, cmap="inferno")
    data_sps = 1 / (per_lap * wlen)

    if fix_colorbar is True:
        ax.images[0].set_clim(-180, -100)  # from experiences

    ax.set_ylim(1, 45)
    ax.set_yticks([1, 10, 20, 30, 40, 45], [1, 10, 20, 30, 40, 45])
    ax.set_ylabel("Frequency [Hz]", weight="bold")

    if cbar_ax is None:
        pass
    else:
        cbar = fig.colorbar(ax.images[0], cax=cbar_ax, orientation="horizontal")
        cbar.set_label("Power Spectral Density (dB)")

    rewrite_x_ticks(
        ax,
        data_start=st.stats.starttime,  # type: ignore
        data_end=st.stats.endtime,  # type: ignore
        data_sps=1,  # fixed for psd
        x_interval=x_interval,
    )

    return ax, data_sps


def plot_st(fig, st, time=None):
    """
    plot the st, either one stream, or multiple streams

    Args:
        output_dir: str,
        output_format: str
        fig: fig
        st: obspy st
        time: str time stamps in list

    Returns:

    """

    if type(st) is Trace:
        st = Stream([st])

    st.plot(fig=fig, handle=True, equal_scale=False, zorder=2)

    ax_list = []
    for idx in range(len(st)):
        ax_list.append(fig.axes[idx])

    if time is not None:
        for ax in ax_list:
            ax.grid(axis="y", color="grey", linestyle="--", lw=0.5, alpha=0.5, zorder=1)

            for idx, t in enumerate(time):
                ax.axvline(pd.to_datetime(t), color="r", linestyle="-", lw=1, zorder=1, label=t)

    # for y label
    fig.text(x=0, y=0.5, s="Amplitude [m/s]", weight="bold", va="center", rotation="vertical")
    # for x label
    fig.text(x=0.5, y=0, s="Time [UTC+0]", fontweight="bold", ha="center")

    return fig, ax_list


def time_series_plot(obspy_streams, time_markers=None, time_markers_label=None):
    """
    Plot the time seris

    Args:
        stream: Obspy Stream, collects all positional arguments into a tuple
        time_markers: list of string time stamps, format by "%Y-%m-%dT%H:%M:%S"
        time_markers_label: custom explanation of your time stamps

    Returns:
        fig, then you can save it to somewhere
    """

    stream_length = len(obspy_streams)

    if time_markers is not None and time_markers_label is not None:
        assert len(time_markers) == len(time_markers_label), "check the length time_markers and time_markers_label"

    fig = plt.figure(figsize=(5.5, 2 * stream_length))
    gs = gridspec.GridSpec(stream_length, 1)
    axes = []

    for idx, st in enumerate(obspy_streams):
        if type(st) is Stream:
            st.merge(method=1, fill_value="latest", interpolation_samples=0)
            st._cleanup()
            st = st[0]

        stats = st.stats  # type: ignore
        data = st.data  # type: ignore

        network = stats.network
        station = stats.station
        location = stats.location
        channel = stats.channel
        sps = stats.sampling_rate

        duration = stats.endtime - stats.starttime
        meta_data = f"{network}-{station}-{location}-{channel}-{sps}"

        if duration >= 12 * 3600:
            x_interval = 4 * 3600
        elif 4 * 3600 <= duration < 12 * 3600:
            x_interval = 2 * 3600
        elif 1 * 3600 < duration < 4 * 3600:
            x_interval = 1 * 3600
        elif 0.5 * 3600 < duration <= 1 * 3600:
            x_interval = 0.25 * 3600  # 15 min
        else:
            x_interval = 5 / 60 * 3600  # 5 min

        ax = plt.subplot(gs[idx])
        axes.append(ax)

        ax.plot(data, color="black", label=meta_data)
        ax.set_xlim(0, data.size)

        if time_markers is not None and time_markers_label is not None:
            color_list = [f"C{i}" for i in range(len(time_markers))]

            for c, (t, s) in enumerate(zip(time_markers, time_markers_label)):
                # give different ls
                if "start" in s:
                    ls = "-"
                else:
                    ls = "--"

                x = (UTCDateTime(t) - st.stats.starttime) * sps  # type: ignore
                ax.axvline(x=x, lw=1, ls=ls, color=color_list[c], zorder=1, label=s)

        ax.legend(fontsize=6)

        xLocation = np.arange(0, st.stats.npts, sps * x_interval)  # type: ignore
        xTicks = [(st.stats.starttime + i * st.stats.delta).strftime("%H:%M:%S") for i in xLocation]  # type: ignore

        ax.set_xticks(xLocation, xTicks)
        ax.set_xlabel(f"UTC+0 Time [{st.stats.starttime.strftime('%Y-%m-%d')}]", fontweight="bold")  # type: ignore

    return fig, axes
