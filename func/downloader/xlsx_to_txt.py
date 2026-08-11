#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-10T15:34:54
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
        usecols = list(range(column_s, column_e)) # select part of the columns
        df = pd.read_excel(input_xlsx_path, engine='openpyxl', header=3, usecols=usecols)

        print(f"Flow-Bnech Metadata\n"
              f"Num of rows: {len(df.index)}\n"
              f"Name of columns: {df.columns}\n\n")

    except Exception as e:
        raise ValueError(f"Exception error.\n{e}")

    df.to_csv(output_txt_path, index=False)
    
    return df
