#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-09-23
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import pandas as pd

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>


def converter(input_xlsx, output_txt):

    try:
        usecols = list(range(0, 15)) # select part of the columns
        df = pd.read_excel(f"{project_root}/data/event_catalog/{input_xlsx}", engine='openpyxl', header=0, usecols=usecols)

        print(df.columns)
    except Exception as e:
        print(f"{e}")
        sys.exit(1)


    df.to_csv(f"{project_root}/data/event_catalog/{output_txt}", index=False)


def main():
    converter(input_xlsx="Flow_Bench_Catalog_work.xlsx", output_txt="Flow_Bench_Catalog_work.txt")


if __name__ == "__main__":
    main()