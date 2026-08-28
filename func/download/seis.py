#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-18T15:25:34
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import pandas as pd

from obspy.clients.fdsn import Client
from obspy import read, Inventory, read_inventory, UTCDateTime, Stream

import urllib.parse

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
from data.meta.paz_meta import load_paz
from func.toolkit.nextcloud_IO import data_exchange
from func.toolkit.load_key import load_nextcloud_key
from func.seismic.remove_response import cooking_recipe


def load_raw_glic(
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
):

    project_root_glic = Path("/storage/vast-gfz-hpc-01/project/seismic_data_qi/seismic")

    year = UTCDateTime(starttime).year
    julday = UTCDateTime(starttime).julday

    sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
    file_name = f"{seis_network}.{seis_station}.{seis_channel}.{year}.{julday:03d}.mseed"

    st_path = Path(project_root_glic) / sub_folder / file_name
    st_raw = read(st_path)

    if save_st is True:
        st_path = Path(project_root) / local_dir / sub_folder / file_name
        st_path.parent.mkdir(parents=True, exist_ok=True)
        st_raw.write(st_path, format="MSEED")

    # only save the inv from GLIC to local for the network with "xml" response
    if save_inv is True and seis_response == "xml":
        inv_path = Path(project_root_glic) / f"{continent}/{seis_cat}/meta_data"
        inv_path_files = os.listdir(inv_path)

        # empty inv to be filled
        inv_or_paz = Inventory(networks=[], source="merged_inventory")
        for i in inv_path_files:
            if i.lower().endswith(".xml"):
                i_path = Path(inv_path) / i
                inv_or_paz = inv_or_paz + read_inventory(i_path, format="STATIONXML")

        # save to local
        sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}"
        file_name = "inventory.xml"
        inv_path = Path(project_root) / local_dir / sub_folder / file_name

        inv_path.parent.mkdir(parents=True, exist_ok=True)
        inv_or_paz.write(inv_path, format="STATIONXML")  # type: ignore

    else:
        inv_or_paz = None

    return st_raw, inv_or_paz


def load_raw_fdsn(
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
):

    if pd.isna(seis_location) is True:
        seis_location = ""

    client = Client(seis_client)

    # gets requested raw data
    st_raw = client.get_waveforms(
        network=seis_network,
        station=seis_station,
        location=seis_location,
        channel=seis_channel,
        starttime=starttime,
        endtime=endtime,
        attach_response=True,
    )

    # gets all available station metadata
    inv_or_paz = client.get_stations(
        network=seis_network,
        station=seis_station,
        location=seis_location,
        channel=seis_channel,
        level="response",
        format="xml",
    )

    # save the file
    year = UTCDateTime(starttime).year
    julday = UTCDateTime(starttime).julday

    # save the st
    if save_st is True:
        sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
        file_name = f"{seis_network}.{seis_station}.{seis_channel}.{year}.{julday:03d}.mseed"

        st_path = Path(project_root) / local_dir / sub_folder / file_name

        st_path.parent.mkdir(parents=True, exist_ok=True)
        st_raw.write(st_path, format="MSEED")  # type: ignore

    # save the inv
    if save_inv is True:
        sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}"
        file_name = "inventory.xml"

        inv_path = Path(project_root) / local_dir / sub_folder / file_name

        # only save it if it is not exist
        if inv_path.exists():
            pass
        else:
            inv_or_paz = client.get_stations(network=seis_network, station=seis_station, level="response", format="xml")
            inv_path.parent.mkdir(parents=True, exist_ok=True)
            inv_or_paz.write(inv_path, format="STATIONXML")  # type: ignore

    return st_raw, inv_or_paz


def load_raw_zenodo(
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
):

    st_raw, inv_or_paz = 1, 2
    raise ValueError("Not ready!")
    # Last modified: 2026-08-17T14:00:34

    return st_raw, inv_or_paz


def load_raw_nextcloud(
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
):

    # get the nextcloud key
    try:
        base_url, share_token, pass_word = load_nextcloud_key(key_name="Nextcloud_key.yml")
    except Exception as e:  # noqa: BLE001
        raise ValueError("Please make sure you have the Nextcloud key at:\n f'/project_root/config/Nextcloud_key.yml' ")

    st_raw = Stream()
    year = UTCDateTime(starttime).year

    for julday in range(UTCDateTime(starttime).julday, UTCDateTime(endtime).julday + 1):
        sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
        file_name = f"{seis_network}.{seis_station}.{seis_channel}.{year}.{julday:03d}.mseed"
        st_raw_path = Path(project_root) / local_dir / sub_folder / file_name

        try:
            # try to load from local first
            st_raw = st_raw + read(st_raw_path)
        except FileNotFoundError:
            # if there is no this file, then, go to nextcloud
            remote_file_path = f"{sub_folder}/{file_name}"
            remote_file_url = f"{base_url.rstrip('/')}/{urllib.parse.quote(remote_file_path, safe='/')}"

            data_exchange(
                purpose="download",
                local_file_path=st_raw_path,
                remote_sub_folder_url=None,
                remote_file_url=remote_file_url,
                share_token=share_token,
                pass_word=pass_word,
            )

            st_raw += read(st_raw_path)
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"Exception error.\n{e}")

    if seis_response == "xml":
        inv_remote_sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}/inventory.xml"
        inv_local_path = Path(project_root) / local_dir / inv_remote_sub_folder
        inv_remote_url = f"{base_url.rstrip('/')}/{urllib.parse.quote(inv_remote_sub_folder, safe='/')}"

        data_exchange(
            purpose="download",
            local_file_path=inv_local_path,
            remote_sub_folder_url=None,
            remote_file_url=inv_remote_url,
            share_token=share_token,
            pass_word=pass_word,
        )

        inv_or_paz = read_inventory(inv_local_path)
    else:
        inv_or_paz = load_paz(sensor_type)

    return st_raw, inv_or_paz


def get_seis(
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
    f_min=1,
    f_max=25,
):

    if pd.isna(seis_location) is True:
        seis_location = ""

    if seis_client in ["Private", "Zenodo"]:
        st_raw, inv_or_paz = load_raw_nextcloud(
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
        )
    else:
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
            save_st=False,
            save_inv=False,
        )

    st_cooked = cooking_recipe(st=st_raw, inv_or_paz=inv_or_paz, f_min=f_min, f_max=f_max)

    return st_raw, st_cooked
