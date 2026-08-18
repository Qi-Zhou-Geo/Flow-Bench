#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-18T16:17:31
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz-potsdam.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd

import urllib.parse

from tqdm import tqdm

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
from func.toolkit.load_key import load_nextcloud_key
from func.toolkit.nextcloud_IO import make_remote_folders, data_exchange


def upload_folder(local_root, remote_root, base_url, share_token, pass_word):

    local_root = Path(local_root)
    remote_root = str(remote_root).strip("/")

    file_list = []
    for p in local_root.rglob("*"):
        if p.is_file() and p.name not in [".DS_Store"]:
            file_list.append(p)

    for local_file_path in tqdm(file_list, desc="local_root >> remote_root:", total=len(file_list), file=sys.stdout):
        rel_path = local_file_path.relative_to(local_root).as_posix()

        remote_sub_folder = f"{remote_root}/{Path(rel_path).parent}".replace("\\", "/")
        remote_file_path = f"{remote_root}/{rel_path}"

        make_remote_folders(
            base_url=base_url, remote_folder=remote_sub_folder, share_token=share_token, pass_word=pass_word
        )
        remote_sub_folder_url = f"{base_url}/{urllib.parse.quote(remote_sub_folder, safe='/')}"
        remote_file_url = f"{base_url}/{urllib.parse.quote(remote_file_path, safe='/')}"

        data_exchange(
            purpose="upload",
            local_file_path=local_file_path,
            remote_sub_folder_url=remote_sub_folder_url,
            remote_file_url=remote_file_url,
            share_token=share_token,
            pass_word=pass_word,
        )


def main():

    base_url, share_token, pass_word = load_nextcloud_key(key_name="Nextcloud_key.yml")

    print(
        "Please make sure:\n"
        "(1) the folder <seis_raw> exists in Nextcloud\n"
        "(2) the key is correct in your local folder <config/Nextcloud_key.yml>\n"
    )

    upload_folder(
        local_root=Path(project_root) / "data/seis_raw",
        remote_root="",  # make this empty if you set the folder as the previous note.
        base_url=base_url,
        share_token=share_token,
        pass_word=pass_word,
    )


if __name__ == "__main__":
    main()
