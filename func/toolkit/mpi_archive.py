#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-04T15:46:47
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
from filelock import FileLock


def dump_as_row(output_dir, output_name, variable_str, *args):
    """
    Append one row to a text file in a multiprocess-safe way.

    Args:
        output_dir (str): directory for output files
        output_name (str): file name without extension
        variable_str (str): first column (string)
        *args: additional values, converted to string and joined by commas,
               if you pass list "my_list", use "*my_list"
    """

    # ensure directory exists (safe even in multiple process)
    os.makedirs(output_dir, exist_ok=True)

    lock_path = os.path.join(output_dir, f"{output_name}.lock")
    if output_name[-4:] == ".txt":
        txt_path = os.path.join(output_dir, f"{output_name}")
    else:
        txt_path = os.path.join(output_dir, f"{output_name}.txt")

    with FileLock(lock_path):  # ensures atomic write across processes  # noqa: SIM117
        with open(txt_path, "a", encoding="utf-8") as f:
            fields = [str(variable_str)] + [str(a) for a in args]
            line = ", ".join(fields)
            f.write(line + "\n")
