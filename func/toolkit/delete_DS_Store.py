#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-03T15:11:02
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz-potsdam.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import shutil

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion


def clean_project(searching_dir, file_name=".DS_Store", delete_folder_name="__pycache__", size_limit_mb=25):
    """
    Clean project the project before publish it.

    Args:
        searching_dir: str, path of the folder
        file_name: str, shit of Mac
        delete_folder_name: str, shit of Python
        size_limit_mb: float or int, maximum file size of a single file, make sure Github can host the file

    Returns:
        None

    """

    for dirpath, dirnames, filenames in os.walk(searching_dir):
        for file in filenames:
            file_path = os.path.join(dirpath, file)

            # check the file size
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > size_limit_mb:
                print(f"Large file (> {size_limit_mb} MB): {file_path} ({size_mb:.2f} MB)")

            # delete the file
            if file == file_name:
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

        # delete the folder
        for dirname in dirnames:
            if dirname == delete_folder_name:
                dir_path = os.path.join(dirpath, dirname)
                try:
                    shutil.rmtree(dir_path)
                    print(f"Deleted directory: {dir_path}")
                except Exception as e:  # noqa: BLE001
                    print(f"Error deleting directory {dir_path}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean the project before publishing.")
    parser.add_argument("--searching_dir", type=Path, default=project_root)
    parser.add_argument("--file_name", type=str, default=".DS_Store")
    parser.add_argument("--delete_folder_name", type=str, default="__pycache__")
    parser.add_argument("--size_limit_mb", type=float, default=25)
    args = parser.parse_args()

    clean_project(
        searching_dir=args.searching_dir,
        file_name=args.file_name,
        delete_folder_name=args.delete_folder_name,
        size_limit_mb=args.size_limit_mb,
    )
