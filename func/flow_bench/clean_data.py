#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-11T11:35:08
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


local_utc_offset_hour = 8
continent = "Asia"

# seis_cat = "Hongqi"
# working_dir = f"/Users/qizhou/Downloads/share_data_JunqinWang/Butuo_Hongqi_Event_01_20260630_20260703/raw_data"

# seis_cat = "Yanmen"
# working_dir = f"/Users/qizhou/Downloads/share_data_JunqinWang/Wenchuan_Yanmen_Event_01_20250702_20250704/raw_data"


seis_cat = "Yanmen"
working_dir = f"/Users/qizhou/Downloads/share_data_JunqinWang/Wenchuan_Yanmen_Event_02_20250824_20250829/raw_data"


working_dir = Path(working_dir)



all_sta = os.listdir(working_dir)
if '.DS_Store' in all_sta:
    all_sta.remove('.DS_Store')

for folder_name in all_sta:
    all_seis_data = os.listdir(f"{working_dir}/{folder_name}")
    
    for file_name in all_seis_data:
        if file_name.lower().endswith(".sac"):
            
            st = read(f"{working_dir}/{folder_name}/{file_name}")
            for tr in st:
                tr.stats.starttime = tr.stats.starttime - local_utc_offset_hour * 3600
                tr.stats.station = folder_name[-4:]
                
            meta_data = st[0].stats
            
            seis_network = meta_data.network
            seis_station = meta_data.station
            seis_channel = meta_data.channel
            
            starttime = meta_data.starttime
            endtime = meta_data.endtime
            year = UTCDateTime(starttime).year
            julday_start = UTCDateTime(starttime).julday
            julday_end = UTCDateTime(endtime).julday
            
            for julday in range(julday_start, julday_end):
                s = UTCDateTime(year=year, julday=julday)
                e = UTCDateTime(year=year, julday=julday) + 24 * 3600
                
                tr = st.copy()
                tr.trim(s, e)
            
                file_name = f"{seis_network}.{seis_station}.{seis_channel}.{year}.{julday}.mseed"
                sub_folder = f"data/raw_seis/{continent}/{seis_cat}/{year}/{seis_station}/{seis_channel}"
                raw_st_path = Path(project_root) / sub_folder / file_name
                raw_st_path.parent.mkdir(parents=True, exist_ok=True)
                
                tr.write(raw_st_path, format="MSEED")
                print(tr[0].stats, raw_st_path)

