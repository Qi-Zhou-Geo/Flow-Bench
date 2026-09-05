#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-03T11:55:17
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion

from func.seismic.denoising import denoise_st


def cal_snr(st, window_size, window_overlap, denoising_method):

    st_copy = st.copy()
    st_copy.merge(method=1, fill_value="latest", interpolation_samples=0)

    low_sampling_rate, denoised_st = denoise_st(
        st=st_copy,
        window_size=window_size,
        window_overlap=window_overlap,
        denoising_method=denoising_method,
        fmt="%Y-%m-%dT%H:%M:%S",
    )

    data = denoised_st[0].data  # type: ignore
    # snr = np.max(data) / np.mean(data)

    snr = np.mean(data) / np.std(data)

    return snr
