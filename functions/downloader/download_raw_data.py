#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-09-23
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os

import requests
import zipfile
from tqdm import tqdm

from pathlib import Path
from urllib.parse import urlparse

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>


def data_downloader(zenodo_url, project_root, output_folder=None):

    output_file_name = Path(zenodo_url).name
    if output_folder is None:
        zip_path = f"{project_root}/data/{output_file_name}"
    else:
        os.makedirs(output_folder, exist_ok=True)
        zip_path = output_folder

    # stream download
    response = requests.get(zenodo_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024 * 2  # 2 MB

    with open(zip_path, "wb") as file, tqdm(
        desc=f"Downloading {output_file_name}",
        total=total_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(block_size):
            file.write(data)
            bar.update(len(data))


    with zipfile.ZipFile(zip_path , 'r') as zip_ref:
        zip_ref.extractall(output_folder)


def main(output_path=f"./data/seismic", raw_data_source="Zenodo"):

    '''
    Download the all raw data from "Flow-Bench" archive.

    Args:
        output_path: str, the path where you want to save the raw seismic data
        raw_data_source: str, the raw data source, either
                        - "Zenodo": the raw data
                        - "FDSN":
                        - "Zenodo-FDSN"

    Returns:
        No return
    '''

    # replace with the actual Zenodo file download link (not just the DOI)
    zenodo_url = "https://zenodo.org/record/17183172/files/seismic.zip"
    output_folder = f"{project_root}/data/seismic"
    data_downloader(zenodo_url, output_folder, project_root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sca_path", type=str, default="glic path", help="check the sac path")
    args = parser.parse_args()

    main(args.sca_path)
