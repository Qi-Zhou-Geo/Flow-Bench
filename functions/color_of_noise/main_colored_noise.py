#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2024-03-21
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do NOT distribute this code without the author's permission

import os
import argparse
from itertools import product

import numpy as np
from scipy.signal import savgol_filter

from obspy import read, Stream, Trace, read_inventory, signal
from obspy.core import UTCDateTime # default is UTC+0 time zone

import matplotlib.ticker as ticker
import matplotlib.pyplot as plt

# import the custom functions
from colored_noise import *


def workflow(noise_type_list, intensity_ratio_list, synth_station="synthetic12"):
    '''
       Generate the Synthetic data-60s to test the model

       Args:
           noise_type: List[str], "white_noise", "pink_noise", "red_noise"
           intensity_ratio: List[float], 1e-3, 5e-3, 1e-2, 1e-1, 1e0

       Returns:
           none,
       '''

    ref_path = "/storage/vast-gfz-hpc-01/project/seismic_data_qi/seismic/EU/Illgraben"
    ref_file = "9S.ILL12.EHZ.2022.156.mseed"  # 2022-06-05
    network, station, component, year, julday, extension = ref_file.split(".")

    st = read(f"{ref_path}/{year}/{station}/{component}/{ref_file}")
    st = st[0]
    st.trim(UTCDateTime("2022-06-05T00:00:00"), UTCDateTime("2022-06-06T00:00:00"))

    for idx, noise_type in enumerate(noise_type_list):
        for idy, intensity_ratio in enumerate(intensity_ratio_list):
            idy = idy + 1
            # make the noise
            white_noise_f, white_noise_t = make_noise(noise_type, st.stats.npts, st.stats.sampling_rate)

            # prepare the st
            intensity = np.max(np.abs(st.data)) * intensity_ratio
            temp_data = np.round(white_noise_t * intensity, 0).astype(st.data.dtype) + st.data
            temp_st = create_trace(temp_data, st.stats.sampling_rate, st)
            temp_st = temp_st[0]
            temp_st.stats.starttime = temp_st.stats.starttime + 24 * 3600 * idy

            output_dir = f"{ref_path}/{year}/{synth_station}/{noise_type.split('_')[0]}"
            output_format = f"{network}.{synth_station}.{noise_type.split('_')[0]}.{year}." \
                            f"{str(int(float(julday) + idy)).zfill(3)}.mseed"
            print(f"{output_dir}, {output_format}, {noise_type}, {intensity_ratio:.0e}")
            os.makedirs(output_dir, exist_ok=True)

            temp_st.write(f"{output_dir}/{output_format}", format="MSEED")


def main(noise_type_list, intensity_ratio_list):
    workflow(noise_type_list, intensity_ratio_list)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='input parameters')

    parser.add_argument("--noise_type_list", nargs="+", type=str, help='e.g., ["white_noise"]')
    parser.add_argument("--intensity_ratio_list", nargs="+", type=float, help='e.g., [1e-3, 1e-2]')

    args = parser.parse_args()

    main(args.noise_type_list, args.intensity_ratio_list)
