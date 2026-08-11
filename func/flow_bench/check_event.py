#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-11T11:59:52
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import yaml

import matplotlib.pyplot as plt

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
from func.downloader.seis import cooking_recipe
from data.meta.seis.paz_meta import load_paz
from func.seismic.welch_spectrum import welch_psd




# Hongqi
working_dir = '/Users/qizhou/#python/Flow-Bench/data/raw_seis/Asia/Hongqi/2026'

t_s = ["2026-07-02T00:16:00Z", "2026-07-02T07:16:00Z", "2026-07-02T09:16:00Z"]
t_e = ["2026-07-02T04:16:00Z", "2026-07-02T08:56:00Z", "2026-07-02T10:16:00Z"]
inv_or_paz = load_paz("unknown-Hongqi")


all_sta = os.listdir(working_dir)
if '.DS_Store' in all_sta:
    all_sta.remove('.DS_Store')


# ['0571', '0578', '0579', '0577', '0574', '0573']
folder_name = '0573'
all_seis_data = os.listdir(f"{working_dir}/{folder_name}/HHZ")

st = Stream()
for file_name in all_seis_data:
    st = st + read(f"{working_dir}/{folder_name}/HHZ/{file_name}")

st.merge(method=1, fill_value='latest', interpolation_samples=0)
st._cleanup()

tr = None
for s, e in zip(t_s, t_e):
    tr = st.copy()
    t1 = UTCDateTime(s) - 3600 *3
    t2 = UTCDateTime(e) + 3600 *3
    tr.trim(t1, t2)
    st_cooked = cooking_recipe(st=tr, inv_or_paz=inv_or_paz, f_min=1, f_max=25)
    st_cooked.plot()




freq, psd, psd_unit = welch_psd(data=st_cooked[0].data, sampling_rate=250, f_min=1, f_max=50, segment_window=10, scaling="density", unit_dB=True)
plt.plot(freq, psd)










# Yanmen
working_dir = '/Users/qizhou/#python/Flow-Bench/data/raw_seis/Asia/Yanmen/2025'

t_s = ["2025-07-02T21:00:00Z", "2025-07-03T13:20:00Z", "2025-08-25T22:20:00Z", "2025-08-27T23:20:00Z"]
t_e = ["2025-07-03T08:40:00Z", "2025-07-03T21:30:00Z", "2025-08-26T07:00:00Z", "2025-08-28T09:00:00Z"]
inv_or_paz = load_paz("unknown-Yanmen")


all_sta = os.listdir(working_dir)
if '.DS_Store' in all_sta:
    all_sta.remove('.DS_Store')


# ['0184', '0183', '0182', '0207', '0206', '0201', '0202', '0194']
folder_name = '0206'
all_seis_data = os.listdir(f"{working_dir}/{folder_name}/HHZ")

st = Stream()
for file_name in all_seis_data:
    st = st + read(f"{working_dir}/{folder_name}/HHZ/{file_name}")
    print(file_name)

st.merge(method=1, fill_value='latest', interpolation_samples=0)
st._cleanup()


tr = None
for s, e in zip(t_s, t_e):
    tr = st.copy()
    t1 = UTCDateTime(s) - 3600 *3
    t2 = UTCDateTime(e) + 3600 *3
    tr.trim(t1, t2)
    st_cooked = cooking_recipe(st=tr, inv_or_paz=inv_or_paz, f_min=1, f_max=25)
    st_cooked.plot()


freq, psd, psd_unit = welch_psd(data=st_cooked[0].data, sampling_rate=250, f_min=1, f_max=50, segment_window=10, scaling="density", unit_dB=True)
plt.plot(freq, psd)