#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
#from brokenaxes import brokenaxes

from scipy.stats import linregress
from scipy.stats import t as student_t  # Student's t-distribution
from scipy.stats import gaussian_kde

from obspy import Stream, Trace, read
from obspy.core import UTCDateTime # default is UTC+0 time zone


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
from func.seismic.seismic_data_processing import load_seismic_signal

catchment_name, seismic_network, station, component = "Wandong", "WD", "STA02", "BHZ"
data_start, data_end = "2023-07-03T00:00:00", "2023-07-04T00:00:00"
f_min, f_max = 1, 100
st = load_seismic_signal(catchment_name, seismic_network, station, component,
                        data_start, data_end,
                        f_min=f_min, f_max=f_max,
                        remove_sensor_response=True)
st.write(f"qq.mseed", format="MSEED")