#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-14T00:53:06
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import yaml

import numpy as np
import pandas as pd

from tqdm import tqdm

from obspy import UTCDateTime, read, Stream, read_inventory


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
from func.downloader.seis import get_seis, cooking_recipe
from func.downloader.seis import load_raw_glic, load_raw_fdsn, load_raw_zenodo, load_raw_nextcloud
from func.toolkit.logger_printer import setup_logger
from func.seismic.round_time import round_time
from data.meta.paz_meta import load_paz

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

        # paramsters
        self.buffer_time = 3 # how long beyond event do you need
        
        # setup logger
        # output_dir = Path(project_root) / "data/seis_raw"
        # log_filename = "archive_glic.log"
        # logger = setup_logger(output_dir=output_dir, log_filename=log_filename, force_reset=True)
        # msg = f"Download raw seismic data and seismic inventory (if available) from GLIC to the local PC.\n\n"
        # logger.info(msg)

    def get_metadata(self, meta_type, print_meta=True):

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

        df_meta = xlsx2txt(input_xlsx_path=meta_xlsx, 
                           output_txt_path=meta_txt, 
                           column_s=column_s, column_e=column_e)
        
        if print_meta is True:
            print(f"Flow-Bnech Metadata\n"
                  f"Num of rows: {len(df_meta.index)}\n"
                  f"Name of columns: {df_meta.columns}\n\n")

        return df_meta

    def get_dem(self, seis_cat, dem_resolutio):

        # from seis_cat to the meta
        dem = self.download_dem(seis_cat, dem_resolutio)

        return dem


    def down_all_seis_data(self, buffer=2, data_source="FDSN"):
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
        
        seis_meta = self.get_metadata(meta_type="seis")
        event_meta = self.get_metadata(meta_type="event")
        client_arr = np.array(seis_meta["seis_client"])
        
        if data_source == "FDSN":
            down_func = load_raw_fdsn
            keep_idx = ~np.isin(client_arr, ["Zenodo", "Private"])
            
            msg = f"Note! You may need 4.5 Gb space to save the data from <data_source>={data_source}\n\n."
            print(msg)
        elif data_source in ["Zenodo", "Nextcloud"]:
            down_func = load_raw_nextcloud #load_raw_zenodo
            keep_idx = np.isin(client_arr, ["Zenodo", "Private"])
            
            msg = f"Note! You may need 4.5 Gb space to save the data from <data_source>={data_source}\n\n."
            print(msg)
        elif data_source == "GLIC":
            down_func = load_raw_glic
            keep_idx = np.isin(client_arr, ["Zenodo", "Private"])
            
            msg = "Warning! Only the development team is allowed to run this step."
            print(msg)
        
            msg = f"Download raw seismic data and seismic inventory (if available) from GLIC to the local PC.\n\n"
            print(msg)
            
            msg = f"Note! You may need 4.5 Gb space to save the data from <data_source>={data_source}\n\n."
            print(msg)
            
        else:
            raise ValueError(f"Unsupported <data_source>: {data_source}")



        seis_meta = seis_meta.loc[keep_idx].reset_index(drop=True)
        event_meta = event_meta.loc[keep_idx].reset_index(drop=True)
        client_list = np.unique(seis_meta["seis_client"]).tolist()
        total_inter = len(seis_meta)
        
        for event_id in tqdm(range(total_inter), 
                             desc=f"Downing data from {data_source}",
                             total=total_inter,
                             file=sys.stdout):
            
            seis_client = seis_meta["seis_client"][event_id]
            if seis_client in client_list:
                
                # region 
                # catchment meta
                continent = seis_meta["continent"][event_id]
                seis_cat = seis_meta["seis_cat"][event_id]

                # seismic meta
                seis_client = seis_meta["seis_client"][event_id]
                seis_network = seis_meta["seis_network"][event_id]
                seis_station = str(seis_meta["seis_station"][event_id])
                seis_location = seis_meta["seis_location"][event_id]
                seis_channel = seis_meta["seis_channel"][event_id]
                seis_response = seis_meta["seis_response"][event_id]
                sensor_type = seis_meta["seis_sensor"][event_id]

                # event meta
                event_t_s = event_meta["event_time_s"][event_id]
                event_t_e = event_meta["event_time_e"][event_id]
                # endregion
                
                year = UTCDateTime(event_t_s).year
                julday = UTCDateTime(event_t_s).julday
                julday_list = np.arange(julday - buffer, julday + buffer + 1)
                
                for j in julday_list:
                    starttime = UTCDateTime(year=year, julday=j)
                    endtime = UTCDateTime(year=year, julday=j) + 24 * 3600
                    
                    try:
                        down_func(continent, seis_cat, 
                                  seis_client, seis_network, 
                                  seis_station, seis_location, seis_channel,
                                  seis_response, sensor_type,
                                  starttime, endtime,
                                  save=True)

                    except Exception as e:
                        msg = (f"Warning! There are not enough data at: {seis_client}.\n"
                            f"{e}\n"
                            f"{continent}-{seis_cat}-{seis_client}-{seis_network}-{seis_station}-{seis_location}-{seis_channel}\n"
                            f"Data is not available: {starttime} to {endtime}.\n\n")
                        print(msg)


    def request_one_seis_event(self, event_id, 
                               starttime=None, endtime=None, 
                               buffer_h=3,
                               f_min=1, f_max=25):

        seis_meta = self.get_metadata(meta_type="seis", print_meta=False)
        event_meta = self.get_metadata(meta_type="event", print_meta=False)

        # region 
        # catchment meta
        continent = seis_meta["continent"][event_id]
        seis_cat = seis_meta["seis_cat"][event_id]

        # seismic meta
        seis_client = seis_meta["seis_client"][event_id]
        seis_network = seis_meta["seis_network"][event_id]
        seis_station = str(seis_meta["seis_station"][event_id])
        seis_location = seis_meta["seis_location"][event_id]
        seis_channel = seis_meta["seis_channel"][event_id]
        seis_response = seis_meta["seis_response"][event_id]
        sensor_type = seis_meta["seis_sensor"][event_id]

        # event meta
        if starttime is None:
            starttime = UTCDateTime(event_meta["event_time_s"][event_id]) - buffer_h * 3600
            
        if endtime is None:
            endtime = UTCDateTime(event_meta["event_time_e"][event_id]) + buffer_h * 3600
            
        starttime = UTCDateTime(round_time(starttime))
        endtime = UTCDateTime(round_time(endtime))
        # endregion
        
        # rquest data
        try:
            # (1) try to load the local cache first
            local_dir = f"data/seis_raw"
            st_raw = Stream()
            
            for julday in range(UTCDateTime(starttime).julday, UTCDateTime(endtime).julday + 1):
                year = UTCDateTime(starttime).year
                
                sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
                file_name = f"{seis_network}.{seis_station}.{seis_channel}.{year}.{julday:03d}.mseed"
                st_raw_path = Path(project_root) / local_dir / sub_folder / file_name
                
                st_raw = st_raw + read(st_raw_path)
            
            if seis_response == "xml":
                inv_path = Path(project_root) / local_dir / f"{continent}/{seis_cat}" / "inventory.xml"
                inv_or_paz = read_inventory(inv_path)
            else:
                inv_or_paz = load_paz(sensor_type=sensor_type)
            
            
            st_cooked = cooking_recipe(st=st_raw, inv_or_paz=inv_or_paz, f_min=f_min, f_max=f_max)
        except FileNotFoundError:
            # (2) if there is no cache, then request the data
            st_raw, st_cooked= get_seis(continent, seis_cat, 
                  seis_client, seis_network, 
                  seis_station, seis_location, seis_channel,
                  seis_response, sensor_type,
                  starttime, endtime,
                  f_min=f_min, f_max=f_max)

        except Exception as e:
            # (3) Unknow error
            raise ValueError(f"Exception error.\n{e}")
        
        st_raw.trim(starttime=starttime, endtime=endtime) # type: ignore
        st_cooked.trim(starttime=starttime, endtime=endtime)
        
        return st_raw, st_cooked


    def get_event_t(self, st):
        pass


def usage():
    fb = FlowBench()

    # download all FSDN data
    fb.down_all_seis_data(buffer=1, data_source="FDSN")

    # load the meta
    seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)
    
    # request the evnet id 160
    st_raw, st_cooked = fb.request_one_seis_event(event_id=160)
    st_raw.plot() # type: ignore
    st_cooked.plot()
