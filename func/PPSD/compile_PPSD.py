#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-05-12
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import argparse

import numpy as np
import pandas as pd

from datetime import datetime


import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable

from obspy.clients.fdsn import Client
from obspy import read, Stream, read_inventory, signal, UTCDateTime

from obspy.signal import PPSD

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
from data.noise_model.visualize_noise_model import plot_noise_model


def define_PPSD(st, inv,
                db_bins=(-200, -60, 1),
                data_length=60 * 32,
                period_range=(0.02, 1)):
    '''
    Create the PPSD object

    Args:
        st: Obspy stream,
        inv: Obspy inv,
        db_bins: tuple, unit by dB, boundary of PSD
        data_length: float, unit by second
        period_range: tuple, freq * period = 1

    Returns:
        PPSD: Obspy PPSD

    '''

    ppsd = PPSD(stats=st[0].stats, metadata=inv,
                skip_on_gaps=True,
                db_bins=db_bins,
                ppsd_length=data_length,  # unit by seconds
                overlap=0.5,
                special_handling=None,
                period_smoothing_width_octaves=1.0,
                period_step_octaves=0.125,
                # unit by second, same as [1 Hz, 50 Hz]
                period_limits=period_range)

    return ppsd


def loop_julday(sca_path, year, station, component, julday):

    st = read(f"{sca_path}/{year}/{station}/{component}/"
              f"9S.{station}.{component}.{year}.{julday}.mseed")

    return st

def get_df_day(year, station):

    df = pd.read_csv(f"{project_root}/data/manually_labeled_DF/9S-{year}-DF.txt", header=0)
    df_arr = np.array(df)

    id = np.where(df_arr[:, 5] == station)[0]
    df_arr = df_arr[id]

    df_list = []
    for i in range(id.size):
        s = UTCDateTime(df_arr[i, 2]).julday
        e = UTCDateTime(df_arr[i, 3]).julday

        df_list.append(s)
        df_list.append(e)
        print(s,e)

    df_list = np.array(df_list)
    df_list = np.unique(df_list)

    return df_list


def main(sca_path, component="EHZ"):

    inv = read_inventory(f"{sca_path}/meta_data/9S_2017_2022.xml")
    ref_st = read(f"{sca_path}/2017/ILL02/{component}"
                  f"/9S.ILL02.EHZ.2017.138.mseed")

    ppsd = define_PPSD(ref_st, inv)
    ppsd_event = define_PPSD(ref_st, inv)
    ppsd_noise = define_PPSD(ref_st, inv)


    j1 = [138, 145, 145, 150]
    j2 = [183, 240, 240, 250]


    for idx, year in enumerate([2017, 2018, 2019, 2020]):

        if year == 2017:
            station = "ILL02"
        else:
            station = "ILL12"

        df_list = get_df_day(year, station)

        for julday in range(j1[idx], j2[idx]+1, 1):

            st = loop_julday(sca_path, year, station, component, str(julday).zfill(3))
            ppsd.add(st)

            if julday in df_list:
                ppsd_event.add(st)
            else:
                ppsd_noise.add(st)

            time_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            print(f"{time_now}, {year}, {station}, {julday}")

        # save and load the file
        ppsd.save_npz(f"{current_dir}/noise_ppsd_{year}_{j1[idx]}_{j2[idx]+1}.npz")
        ppsd_event.save_npz(f"{current_dir}/noise_ppsd_{year}_event.npz")
        ppsd_noise.save_npz(f"{current_dir}/noise_ppsd_{year}_noise.npz")
        #ppsd = PPSD.load_npz("/Users/qizhou/Desktop/noise_ppsd.npz")



    ppsd.save_npz(f"{current_dir}/noise_ppsd_2017_2020.npz")
    ppsd_event.save_npz(f"{current_dir}/noise_ppsd_2017_2020_event.npz")
    ppsd_noise.save_npz(f"{current_dir}/noise_ppsd_2017_2020_noise.npz")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sca_path", type=str, default="glic path", help="check the sac path")
    args = parser.parse_args()

    main(args.sca_path)
