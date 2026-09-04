#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-03T10:50:57
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

from obspy.clients.fdsn import Client
from obspy import UTCDateTime


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
