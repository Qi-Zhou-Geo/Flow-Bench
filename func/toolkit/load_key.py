#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-17T14:03:05
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import yaml

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion


def load_key(key_name):

    try:
        key_path = Path(project_root) / f"config/{key_name}"
        with open(key_path, "r") as f:
            config = yaml.safe_load(f)
            API_Key = config["API_Key"]
    except FileNotFoundError:
        raise ValueError(f"Please regeist your {key_name} key.")

    return API_Key


def load_nextcloud_key(key_name):

    try:
        key_path = Path(project_root) / f"config/{key_name}"
        with open(key_path, "r") as f:
            config = yaml.safe_load(f)

            base_url = config["base_url"]
            share_token = config["share_token"]
            pass_word = config["pass_word"]
    except FileNotFoundError:
        raise ValueError(f"Please regeist your {key_name} key.")

    return base_url, share_token, pass_word
