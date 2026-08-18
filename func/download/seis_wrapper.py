#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-18T16:16:32
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

from tqdm import tqdm

import numpy as np
from obspy import read, Stream, read_inventory, UTCDateTime


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
from func.seismic.round_time import round_time
from func.seismic.remove_response import cooking_recipe
from func.download.seis import load_raw_fdsn, load_raw_nextcloud, load_raw_glic, get_seis


def all_seis_data(seis_meta, event_meta, buffer, data_source):
    """
    Download the alll debris-flow seismic records.

    Args:
        buffer (int, optional): Number of Julian days to extend around each event.
            For example, if an event occurs on Julian day j and buffer=1,
            data from Julian days [j-1, j, j+1] will be downloaded.

            Note: Zenodo or private data sources may not include this full time range,
            because the original released data may be shorter.

            Defaults to 1.

        data_source (str, optional): Data source to use. Options are "FDSN", "Zenodo", or "GLIC".
            "FDSN" denotes data hosted on an FDSN server.
            "Zenodo" and "GLIC" denote data from peer-reviewed papers,
            which are archived either on the GFZ GLIC server or in publicly accessible Zenodo repositories.

            Defaults to "FDSN".
    """

    # copy the df frame
    seis_meta_copy, event_meta_copy = seis_meta.copy(), event_meta.copy()
    client_arr = np.array(seis_meta_copy["seis_client"])

    if data_source == "FDSN":
        down_func = load_raw_fdsn
        keep_idx = ~np.isin(client_arr, ["Zenodo", "Private"])

        msg = f"Note! You may need 4.5 Gb space to save the data from <data_source>={data_source}\n\n."
        print(msg)
    elif data_source in ["Zenodo", "Nextcloud"]:
        # load_raw_zenodo not supported so far. 2026-08-16T17:08:50
        down_func = load_raw_nextcloud
        keep_idx = np.isin(client_arr, ["Zenodo", "Private"])

        msg = f"Note! You may need 4.5 Gb space to save the data from <data_source>={data_source}\n\n."
        print(msg)
    elif data_source == "GLIC":
        down_func = load_raw_glic
        keep_idx = np.isin(client_arr, ["Zenodo", "Private"])

        msg = "Warning! Only the development team is allowed to run this step.\n"
        print(msg)

        msg = "Download raw seismic data and seismic inventory (if available) from GLIC to the local PC.\n"
        print(msg)

        msg = f"Note! You may need 4.5 Gb space to save the data from <data_source>={data_source}\n\n."
        print(msg)
    else:
        raise ValueError(f"Unsupported <data_source>: {data_source}")

    seis_meta_copy = seis_meta_copy.loc[keep_idx].reset_index(drop=True)
    event_meta_copy = event_meta_copy.loc[keep_idx].reset_index(drop=True)
    client_list = np.unique(seis_meta_copy["seis_client"]).tolist()
    total_inter = len(seis_meta_copy)

    for event_id in tqdm(
        range(total_inter), desc=f"Downing data from {data_source}", total=total_inter, file=sys.stdout
    ):
        seis_client = seis_meta_copy["seis_client"][event_id]
        if seis_client in client_list:
            # region
            # catchment meta
            continent = seis_meta_copy["continent"][event_id]
            seis_cat = seis_meta_copy["seis_cat"][event_id]

            # seismic meta
            seis_client = seis_meta_copy["seis_client"][event_id]
            seis_network = seis_meta_copy["seis_network"][event_id]
            seis_station = str(seis_meta_copy["seis_station"][event_id])
            seis_location = seis_meta_copy["seis_location"][event_id]
            seis_channel = seis_meta_copy["seis_channel"][event_id]
            seis_response = seis_meta_copy["seis_response"][event_id]
            sensor_type = seis_meta_copy["seis_sensor"][event_id]

            # event meta
            event_t_s = event_meta_copy["event_time_s"][event_id]
            event_t_e = event_meta_copy["event_time_e"][event_id]
            # endregion

            year = UTCDateTime(event_t_s).year
            julday = UTCDateTime(event_t_s).julday
            julday_list = np.arange(julday - buffer, julday + buffer + 1)

            for j in julday_list:
                starttime = UTCDateTime(year=year, julday=j)
                endtime = UTCDateTime(year=year, julday=j) + 24 * 3600

                # only save the inv once, this step takes a lot time
                if j == julday:
                    save_inv = True
                else:
                    save_inv = False

                try:
                    down_func(
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
                        save_st=True,
                        save_inv=save_inv,
                    )

                except Exception as e:  # noqa: BLE001
                    msg = (
                        f"Warning! There are not enough data at: {seis_client}.\n"
                        f"{e}\n"
                        f"{continent}-{seis_cat}-{seis_client}-{seis_network}-{seis_station}-{seis_location}-{seis_channel}\n"
                        f"Data is not available: {starttime} to {endtime}.\n\n"
                    )
                    print(msg)


def one_seis_event(seis_meta, event_meta, event_id, starttime, endtime, f_min, f_max):

    # copy the df frame
    seis_meta_copy, event_meta_copy = seis_meta.copy(), event_meta.copy()

    # region
    # catchment meta
    continent = seis_meta_copy["continent"][event_id]
    seis_cat = seis_meta_copy["seis_cat"][event_id]

    # seismic meta
    seis_client = seis_meta_copy["seis_client"][event_id]
    seis_network = seis_meta_copy["seis_network"][event_id]
    seis_station = str(seis_meta_copy["seis_station"][event_id])
    seis_location = seis_meta_copy["seis_location"][event_id]
    seis_channel = seis_meta_copy["seis_channel"][event_id]
    seis_response = seis_meta_copy["seis_response"][event_id]
    sensor_type = seis_meta_copy["seis_sensor"][event_id]

    # event meta
    event_t_s = event_meta_copy["event_time_s"][event_id]
    event_t_e = event_meta_copy["event_time_e"][event_id]

    starttime = UTCDateTime(round_time(starttime))
    endtime = UTCDateTime(round_time(endtime))
    # endregion

    # rquest data
    try:
        # (1) try to load the local cache first
        local_dir = "data/seis_raw"
        st_raw = Stream()

        year = UTCDateTime(starttime).year

        for julday in range(UTCDateTime(starttime).julday, UTCDateTime(endtime).julday + 1):
            sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
            file_name = f"{seis_network}.{seis_station}.{seis_channel}.{year}.{julday:03d}.mseed"
            st_raw_path = Path(project_root) / local_dir / sub_folder / file_name

            st_raw = st_raw + read(st_raw_path)

        if seis_response == "xml":
            sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}"
            file_name = "inventory.xml"

            inv_path = Path(project_root) / local_dir / sub_folder / file_name

            inv_or_paz = read_inventory(inv_path)
        else:
            inv_or_paz = load_paz(sensor_type=sensor_type)

        st_cooked = cooking_recipe(st=st_raw, inv_or_paz=inv_or_paz, f_min=f_min, f_max=f_max)

        print(f"Load the data from local_dir: {local_dir}")
    except FileNotFoundError:
        # (2) if there is no cache, then request the data
        st_raw, st_cooked = get_seis(
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
            f_min=f_min,
            f_max=f_max,
        )

    except Exception as e:  # noqa: BLE001
        # (3) Unknow error
        raise ValueError(f"Exception error.\n{e}")

    st_raw.trim(starttime=starttime, endtime=endtime)  # type: ignore
    st_cooked.trim(starttime=starttime, endtime=endtime)

    return st_raw, st_cooked
