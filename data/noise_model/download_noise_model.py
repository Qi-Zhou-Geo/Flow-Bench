#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
from obspy.signal.spectral_estimation import get_nhnm, get_nlnm

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>


periods, hnm = get_nhnm()  # High Noise Model
periods, lnm = get_nlnm()  # Low Noise Model

np.savez(f"{project_root}/data/noise_model/high-noise-model-Peterson1993.npz", periods=periods, hnm=hnm)
np.savez(f"{project_root}/data/noise_model/low-noise-model-Peterson1993.npz", periods=periods, lnm=lnm)
