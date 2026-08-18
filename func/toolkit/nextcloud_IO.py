#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-18T15:15:42
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz-potsdam.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd

import requests
import urllib.parse


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


def data_exchange(purpose, local_file_path, remote_sub_folder_url, remote_file_url, share_token, pass_word):

    # Local >> Remote
    if purpose == "upload":
        with open(local_file_path, "rb") as data:
            # make folder
            mkcol_resp = requests.request(method="MKCOL", url=remote_sub_folder_url, auth=(share_token, pass_word))
            # ignore if "remote folder" already exists
            if mkcol_resp.status_code not in (201, 405, 409, 301, 302):
                mkcol_resp.raise_for_status()

            # upload file, overwritr by default
            response = requests.put(url=remote_file_url, data=data, auth=(share_token, pass_word))

        response.raise_for_status()

    # Remote >> Local
    elif purpose == "download":
        response = requests.get(remote_file_url, auth=(share_token, pass_word))
        response.raise_for_status()

        local_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_file_path, "wb") as data:
            data.write(response.content)

    else:
        raise ValueError(f"check your purpose: {purpose}")

    return response


def make_remote_folders(base_url, remote_folder, share_token, pass_word):

    current = ""

    for part in remote_folder.split("/"):
        if part == "":
            continue

        current = f"{current}/{part}" if current else part
        folder_url = f"{base_url.rstrip('/')}/{urllib.parse.quote(current, safe='/')}"

        response = requests.request(
            method="MKCOL",
            url=folder_url,
            auth=(share_token, pass_word),
        )

        # 201 = created, 405 = already exists
        if response.status_code not in (201, 405):
            response.raise_for_status()
