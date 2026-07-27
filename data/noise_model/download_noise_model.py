#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-07-27T14:29:45
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
from obspy.signal.spectral_estimation import get_nhnm, get_nlnm

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion



periods, hnm = get_nhnm()  # High Noise Model
periods, lnm = get_nlnm()  # Low Noise Model

np.savez(f"{project_root}/data/noise_model/high-noise-model-Peterson1993.npz", periods=periods, hnm=hnm)
np.savez(f"{project_root}/data/noise_model/low-noise-model-Peterson1993.npz", periods=periods, lnm=lnm)
