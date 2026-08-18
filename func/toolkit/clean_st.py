#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-18T16:14:57
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

from obspy import read, Stream

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion


def clean_data(sub_folder="European/Illgraben/2021/ILL12/EHZ", file_name="9S.ILL12.EHZ.2021.173.mseed"):

    st = Stream()

    temp_st_path = Path(project_root) / f"data/seis_raw/{sub_folder}/{file_name}"
    temp_st = read(temp_st_path)

    for tr in temp_st:
        if tr.stats.sampling_rate == 100:
            st = st + tr

    st.merge(method=1, fill_value="latest", interpolation_samples=0)
    st.write(temp_st_path, format="MSEED")

    st.plot()


if __name__ == "__main__":
    clean_data()
