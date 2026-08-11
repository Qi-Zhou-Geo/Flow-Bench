#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-10T22:28:39
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import yaml

import numpy as np
import pandas as pd

from obspy import UTCDateTime, read, Stream


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
from func.downloader.xlsx_to_txt import xlsx2txt
from func.downloader.dem import download_dem
from func.downloader.seis import download_seis


class FlowBench:

    def __init__(self,
                 version="v2dot1dot1",
                 project_root=None,
                 min_storage=1):

        # specific the data version
        self.version = version

        # I/O dir
        self.project_root = project_root
        self.min_storage = min_storage

        # func
        self.download_dem = download_dem
        self.download_seis = download_seis
        self.xlsx2txt = xlsx2txt

        # paramsters
        self.buffer_time = 3 # how long beyond event do you need

    def get_metadata(self, meta_type):

        meta_xlsx = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{self.version}.xlsx"
        meta_txt = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{self.version}.txt"

        if meta_type == "all":
            column_s, column_e = 17, 19
        elif meta_type == "seis":
            column_s, column_e = 0, 12
        elif meta_type == "dem":
            column_s, column_e = 0, 12
        elif meta_type == "event":
            column_s, column_e = 17, 19
        else:
            raise ValueError(f"Unsupported meta_type: {meta_type}")  

        df_meta = self.xlsx2txt(input_xlsx_path=meta_xlsx, 
                                output_txt_path=meta_txt, 
                                column_s=column_s, column_e=column_e)

        return df_meta

    def get_dem(self, seis_cat, dem_resolutio):

        # from seis_cat to the meta
        dem = self.download_dem(seis_cat, dem_resolutio)

        return dem


    def get_one_seis(self, seis_meta, event_meta, event_id, buffer_time):

        # catchment meta
        continent = seis_meta["continent"][event_id]
        seis_cat = seis_meta["seis_cat"][event_id]

        # seismic meta
        seis_client = seis_meta["seis_client"][event_id]
        seis_network = seis_meta["seis_network"][event_id]
        seis_station = seis_meta["seis_station"][event_id]
        seis_location = seis_meta["seis_location"][event_id]
        seis_channel = seis_meta["seis_channel"][event_id]
        seis_response = seis_meta["seis_response"][event_id]
        sensor_type = seis_meta["seis_sensor"][event_id]

        # event meta
        event_t_s = event_meta["event_time_s"][event_id]
        event_t_e = event_meta["event_time_e"][event_id]

        # rquest data time
        year = UTCDateTime(event_t_s).year
        julday = UTCDateTime(event_t_s).julday


        # file folder and name
        file_name = f"{seis_network}.{seis_station}.{seis_channel}.{year}.{julday}.mseed"

        sub_folder = f"data/raw_seis/{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
        raw_st_path = Path(project_root) / sub_folder / file_name

        sub_folder = f"data/cooked_seis/{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
        cooked_st_path = Path(project_root) / sub_folder / file_name

        try:
            # try to load the local cache first
            raw_st = read(raw_st_path)
            cooked_st = read(cooked_st_path) 
        except FileNotFoundError:
            # if there is no cache, then request the data
            raw_st, cooked_st = self.download_seis(continent, seis_cat, 
                  seis_client, seis_network, 
                  seis_station, seis_location, seis_channel,
                  seis_response, sensor_type,
                  
                  starttime=event_t_s, endtime=event_t_e,
                  buffer_time=buffer_time,
                  )

            raw_st_path.parent.mkdir(parents=True, exist_ok=True)
            raw_st.write(raw_st_path, format="MSEED") # type: ignore

            cooked_st_path.parent.mkdir(parents=True, exist_ok=True)
            cooked_st.write(raw_st_path, format="MSEED") # type: ignore
        except Exception as e:
            raise ValueError(f"Exception error.\n{e}")

        return raw_st, cooked_st

    def get_seis(self, event_id=None, buffer_time=None):

        seis_meta = self.get_metadata(meta_type="seis")
        event_meta = self.get_metadata(meta_type="event")

        if event_id is None:
            # load all data
            request_id = np.arange(len(seis_meta))
        elif isinstance(event_id, (list, tuple, np.ndarray)):
            # only request part of the data
            request_id = event_id
        else:
            # only request one data
            request_id = (event_id, ) # add , make it iterable

        if buffer_time is None:
            buffer_time = self.buffer_time


        raw_st_dict, cooked_st_dict = {}, {}
        for e_idx in request_id:
            raw_st, cooked_st = self.get_one_seis(seis_meta=seis_meta, 
                                                      event_meta=event_meta, 
                                                      event_id=e_idx, 
                                                      buffer_time=self.buffer_time)
            raw_st_dict[e_idx] = raw_st
            cooked_st_dict[e_idx] = cooked_st

        return raw_st_dict, cooked_st_dict

    def get_event_t(self, st):
        pass


def usage():
    fb = FlowBench()
    
    seis_meta = fb.get_metadata(meta_type="seis")
    event_meta = fb.get_metadata(meta_type="event")
    
    seis_meta, event_meta = fb.get_seis(event_id=81)
    
