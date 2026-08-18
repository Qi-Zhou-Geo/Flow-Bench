#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-17T09:54:15
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission


import pandas as pd

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion


def xlsx2txt(input_xlsx_path, output_txt_path, column_s, column_e):

    try:
        usecols = list(range(column_s, column_e))  # select part of the columns
        df = pd.read_excel(input_xlsx_path, engine="openpyxl", sheet_name=0, header=3, usecols=usecols)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Exception error.\n{e}")

    df.to_csv(output_txt_path, index=False)

    return df
