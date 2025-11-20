#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-09-23
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import argparse

import yaml
import pandas as pd

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>


def converter(input_xlsx, output_txt, num_column):

    try:
        usecols = list(range(0, num_column)) # select part of the columns
        df = pd.read_excel(f"{project_root}/data/event_catalog/{input_xlsx}", engine='openpyxl', header=0, usecols=usecols)

        print(f"num_row={len(df.index)}"
              f"\n{df.columns}")

    except Exception as e:
        print(f"{e}")
        sys.exit(1)


    df.to_csv(f"{project_root}/data/event_catalog/{output_txt}", index=False)

def change_data_version(old_version, new_version):

    default_data_path = f"{project_root}/config/data_path.yaml"
    with open(default_data_path, "r", encoding="utf-8") as f:
        text = f.read()

    try:
        text = text.replace(old_version, new_version)
    except Exception as e:
        print(f"{e}\n"
              f"Please check the version number in '{default_data_path}',"
              f"you may need to change it 'old_version {old_version} -> new_version {new_version}' manually.")

    with open(default_data_path, "w", encoding="utf-8") as f:
        f.write(text)


def main(old_version, new_version, num_column=21):

    converter(input_xlsx=f"Flow_Bench_Catalog_vdot{new_version}.xlsx",
              output_txt=f"Flow_Bench_Catalog_work_v0dot{new_version}.txt",
              num_column=num_column)

    change_data_version(old_version, new_version)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--old_version", type=str, default="4-5")
    parser.add_argument("--new_version", type=str, default="6-0")
    # set 19 for define_s_e, set 21 for fit_slope
    parser.add_argument("--num_column", type=int, default=21)
    args = parser.parse_args()

    print("set <num_column> as 19 for define_s_e,\n"
          "set <num_column> as 21 for fit_slope")
    main(args.old_version, args.new_version)