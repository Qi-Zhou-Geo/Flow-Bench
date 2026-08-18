#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-16T17:00:13
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import tempfile
import requests

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

# import the custom functions


def check_response(r):

    if r.ok:
        pass
    else:
        raise RuntimeError(f"{r.status_code}: {r.text}")

    return r


def create_new_draft(latest_record_id, API_Key, headers):

    r = requests.post(
        f"https://zenodo.org/api/deposit/depositions/{latest_record_id}/actions/newversion",
        headers=headers,
    )
    check_response(r)

    latest_draft_url = r.json()["links"]["latest_draft"]
    draft = check_response(requests.get(latest_draft_url, headers=headers)).json()

    deposition_id = draft["id"]
    bucket_url = draft["links"]["bucket"]

    return deposition_id, bucket_url


def zip_and_upload(folder_zip_name, folder_to_zenodo, bucket_url, headers):

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_base = Path(tmpdir) / folder_zip_name.replace(".zip", "")
        zip_path = shutil.make_archive(
            base_name=str(zip_base),
            format="zip",
            root_dir=folder_to_zenodo,
        )

        with open(zip_path, "rb") as fp:
            r = requests.put(
                f"{bucket_url}/{folder_zip_name}",
                data=fp,
                headers=headers,
            )
        check_response(r)

    print("Check the Zenodo draft page before publishing.")
