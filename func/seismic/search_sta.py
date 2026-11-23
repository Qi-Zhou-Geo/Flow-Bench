#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-06T14:17:40
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

from obspy.clients.fdsn import Client
from obspy import UTCDateTime, Stream

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
from func.download.seis import load_raw_fdsn
from func.seismic.remove_response import cooking_recipe
from func.seismic.plot_obspy_st import time_series_plot, psd_plot


def filter_inv(inv, min_sps_hz, removed_network=None):

    # (1) filter by network
    if removed_network is not None:
        filtered_networks = []

        for network in inv:
            if network.code not in removed_network:
                filtered_networks.append(network)

        inv.networks = filtered_networks

    # (2) filter by minimum sampling rate
    for network in inv:
        for station in network:
            filtered_channels = []

            for channel in station.channels:
                if channel.sample_rate >= min_sps_hz:
                    filtered_channels.append(channel)

            station.channels = filtered_channels

    # (3) remove empty stations
    for network in inv:
        filtered_stations = []

        for station in network.stations:
            if len(station.channels) > 0:
                filtered_stations.append(station)

        network.stations = filtered_stations

    # (4) remove empty networks
    filtered_networks = []

    for network in inv:
        if len(network.stations) > 0:
            filtered_networks.append(network)

    inv.networks = filtered_networks

    return inv


def search_seis_sta(
    # seismic meta
    seis_client,
    seis_channel,
    min_sps_hz,
    # event meta
    starttime,
    endtime,
    # target center and radius
    lat,  # degree, S >> add -
    lon,  # degree, W >> add -
    radius_km=50,
    # default
    removed_network=None,
):

    # (1) define the client
    client = Client(seis_client)

    # (2) prepare the input
    starttime = UTCDateTime(starttime)
    endtime = UTCDateTime(endtime)
    radius_deg = radius_km / 111.2  # approximate conversion: 1 degree is around 111.2 km

    # (3) get the inventory
    inv = client.get_stations(
        # target center and radius
        latitude=lat,
        longitude=lon,
        maxradius=radius_deg,
        # event meta
        starttime=starttime,
        endtime=endtime,
        # only for the z component
        channel=f"*{seis_channel}",
        level="channel",
    )

    # (4) filter the SPS
    try:
        inv = filter_inv(inv=inv, min_sps_hz=min_sps_hz, removed_network=removed_network)
    except Exception as e:  # noqa: BLE001
        print(e)
        raise ValueError("Error from <filter_sps>.")

    # (5) check again
    if len(inv) == 0:  # type: ignore
        raise ValueError(
            f"No station was found for:\n"
            f"latitude: {lat}\n"
            f"longitude: {lon}\n"
            f"radius: {radius_km} km\n"
            f"time: {starttime} to {endtime}"
        )
    else:
        pass

    return inv


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

    st_cooked_all = Stream()
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
                    st_cooked_all = st_cooked_all + st_cooked

                    # plot the waveform
                    fig, axes = time_series_plot(obspy_streams=st_cooked, time_markers=None, time_markers_label=None)

                    png_name = f"plots/find_best_data/{seis_cat}_{starttime.julday:03d}/{file_name}_waveform.png"
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

    return st_cooked_all


def usage():

    # 46.199347°N 122.189968°W for Mt. Helens
    inv = search_seis_sta(
        # seismic meta
        seis_client="IRIS",
        seis_channel="Z",
        min_sps_hz=100,
        # event meta
        starttime="2014-10-22T12:00:00",
        endtime="2014-10-22T23:00:00",
        # target center and radius
        lat=46.199347,
        lon=-122.189968,
        radius_km=15,
        # default
        removed_network="1D",
    )

    for network in inv:  # type: ignore
        for station in network:
            for channel in station:
                print(network.code, station.code, channel.code, channel.latitude, channel.longitude)
