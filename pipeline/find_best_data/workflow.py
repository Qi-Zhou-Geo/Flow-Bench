#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-04T10:25:58
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import matplotlib.pyplot as plt
from matplotlib import gridspec

from obspy import UTCDateTime

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
from func.seismic.search_sta import search_seis_sta

from func.seismic.remove_response import cooking_recipe
from func.download.seis import load_raw_fdsn

from func.seismic.plot_obspy_st import time_series_plot, psd_plot


def check_nearby_station(
    # related to event
    starttime,
    endtime,
    # seismic meta
    continent,
    seis_cat,
    # search meta
    seis_client,
    lat,
    lon,
    min_sps_hz=100,
    radius_km=15,
    removed_network="9S",  # this is for non-Illgraben data
    # plot meta
    f_min=1,
    f_max=25,
    seis_response="xml",
    sensor_type="do-not-need-here",
    fmt="%Y-%m-%dT%H:%M:%S",
):

    inv = search_seis_sta(
        # seismic meta
        seis_client=seis_client,
        seis_channel="Z",
        min_sps_hz=min_sps_hz,
        # event meta
        starttime=starttime,
        endtime=endtime,
        # target center and radius
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        removed_network=removed_network,
    )

    print(inv)
    for network in inv:  # type: ignore
        for station in network:
            for channel in station:
                # assign the meta
                seis_network = network.code
                seis_station = station.code
                seis_location = channel.location_code
                seis_channel = channel.code

                # event meta
                starttime = UTCDateTime(starttime)
                endtime = UTCDateTime(endtime)

                file_name = f"{seis_network}-{seis_station}-{seis_location}-{seis_channel}-{starttime.strftime(fmt)}-{endtime.strftime(fmt)}"

                try:
                    st_raw, inv_or_paz = load_raw_fdsn(
                        # catchment meta
                        continent,
                        seis_cat,
                        # seismic meta
                        seis_client,
                        seis_network,
                        seis_station,
                        seis_location,
                        seis_channel,
                        # response meta
                        seis_response,
                        sensor_type,
                        # event meta
                        starttime,
                        endtime,
                        # default params
                        save_st=False,
                        save_inv=False,
                        local_dir="data/seis_raw",
                    )

                    st_cooked = cooking_recipe(st=st_raw, inv_or_paz=inv_or_paz, f_min=f_min, f_max=f_max)

                    # plot the waveform
                    fig, axes = time_series_plot(obspy_streams=st_cooked, time_markers=None, time_markers_label=None)

                    png_name = f"pipeline/find_best_data/{seis_cat}_{starttime.julday:03d}/{file_name}_waveform.png"
                    png_path = Path(project_root) / png_name
                    png_path.parent.mkdir(parents=True, exist_ok=True)

                    plt.tight_layout()
                    plt.savefig(png_path, dpi=600)
                    plt.close(fig)

                    # plot the psd
                    fig = plt.figure(figsize=(5.5, 4))
                    gs = gridspec.GridSpec(2, 1, height_ratios=[10, 1])

                    ax, cbar_ax = plt.subplot(gs[0]), plt.subplot(gs[1])
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

                    ax = plt.subplot(gs[0])
                    ax.set_ylim(1, 25)
                    ax.set_yticks([1, 5, 10, 15, 20, 25], [1, 5, 10, 15, 20, 25])

                    png_name = f"pipeline/find_best_data/{seis_cat}_{starttime.julday:03d}/{file_name}_psd.png"
                    png_path = Path(project_root) / png_name
                    png_path.parent.mkdir(parents=True, exist_ok=True)
                    plt.tight_layout()
                    plt.savefig(png_path, dpi=600)
                    plt.close(fig)

                except Exception as e:  # noqa: BLE001
                    print(fmt, e)
