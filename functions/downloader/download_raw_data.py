#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-09-23
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os

import argparse

from ruamel.yaml import YAML

import numpy as np
import pandas as pd

import requests
from tqdm import tqdm
from urllib.parse import urlparse

import zipfile
import py7zr

from pathlib import Path

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy

project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>


def zenodo_downloader(zenodo_url, output_folder=None, compressed_type="7z"):

    temp_compressed = f"{output_folder}/temp.{compressed_type}"

    # stream download
    response = requests.get(zenodo_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024 * 2  # 2 MB

    with open(temp_compressed, "wb") as f, tqdm(
        desc=f"Downloading raw data from: {zenodo_url}",
        total=total_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(block_size):
            file.write(data)
            bar.update(len(data))

    if compressed_type == "7z":
        with py7zr.SevenZipFile(temp_compressed, mode='r') as archive:
            archive.extractall(path=output_folder)
    elif compressed_type == "zip":
        with zipfile.ZipFile(temp_compressed, mode='r') as archive:
            archive.extractall(path=output_folder)
    else:
        print(f"Error! please check the file compressed type {compressed_type}.")

    # Delete temp file
    os.remove(temp_compressed)

def single_downloader(output_folder, continent, catchment,
                      client_name, network, station, location, channel, start_time, end_time,
                      before, after):

    start_time = UTCDateTime(start_time)
    end_time = UTCDateTime(end_time)
    client = Client(client_name)

    year = start_time.year
    julian_day = np.arange(int(start_time.julday - before), int(end_time.julday + after + 1), 1)

    for idy, j in enumerate(julian_day):

        start_time = UTCDateTime(year=year, julday=j)
        end_time = start_time + 3600 * 24 + 1
        st = client.get_waveforms(network=network, station=station,
                                  location=location, channel=channel,
                                  starttime=start_time, endtime=end_time)

        try:
            st.merge(method=1, fill_value='latest', interpolation_samples=0)
        except Exception as e:
            print(e)

        output_dir = f"{output_folder}/seismic/{continent}/{catchment}/{start_time.year}/{station}/{channel}"
        os.makedirs(name=output_dir, exist_ok=True)
        file_name = f"{network}.{station}.{channel}.{start_time.year}.{str(start_time.julday).zfill(3)}"
        st.write(f"{output_dir}/{file_name}.mseed", format="MSEED")

        inv = client.get_stations(starttime=start_time, endtime=end_time,
                                  network=network, station=station,
                                  location=location, channel=channel,
                                  level="response", format="xml")

        output_dir = f"{output_folder}/seismic/{continent}/{catchment}/meta_data"
        os.makedirs(name=output_dir, exist_ok=True)
        inv.write(f"{output_dir}/{network}_{start_time.year}_{j}.xml", format="STATIONXML")

        print(f"Done {file_name},\n"
              f"saved to {output_dir}")

def fdsn_downloader(arr, output_folder, before, after):

    total_steps = arr.shape[0] * before * after

    for idx in tqdm(range(arr.shape[0]),
                    desc=f"Downloading raw data from FDSN",
                    total=total_steps):

        continent = arr[idx, 1]
        catchment = arr[idx, 2]
        client_name = arr[idx, 5]

        network, station, location, channel = arr[idx, 6], arr[idx, 7], arr[idx, 8], arr[idx, 9]
        start_time, end_time = arr[idx, 12], arr[idx, 13]

        if location == "empty":
            location = ""
        else:
            pass

        single_downloader(output_folder, continent, catchment,
                          client_name, network, station, location, channel, start_time, end_time,
                          before, after)

def merge_stationxml(output_folder):

    for root, _, files in os.walk(output_folder):
        xml_files = [f for f in files if f.endswith(".xml")]
        if not xml_files:
            continue

        # Group XMLs by (network, year)
        grouped = {}
        for f in xml_files:
            name = os.path.splitext(f)[0]  # remove .xml
            parts = name.split("_")
            if len(parts) >= 3:
                network, year = parts[0], parts[1]
                grouped.setdefault((network, year), []).append(os.path.join(root, f))

        # Merge within each group
        for (network, year), paths in grouped.items():
            inv = None
            for p in paths:
                try:
                    inv_part = read_inventory(p)
                    if inv is None:
                        inv = inv_part
                    else:
                        inv += inv_part
                except Exception as e:
                    print(f"Error reading {p}: {e}")

            if inv:
                out_path = os.path.join(root, f"{network}_{year}.xml")
                try:
                    inv.write(out_path, format="STATIONXML")

                    # Delete partial XML files
                    for old_path in paths:
                        if old_path != out_path:  # avoid deleting merged file itself
                            os.remove(old_path)

                except Exception as e:
                    print(f"Error writing {out_path}: {e}")

def main(output_folder=None,
         zenodo_url="https://zenodo.org/record/17432440/files/seismic.7z"):

    # Download the all raw data from "Flow-Bench" archive.
    #zenodo_url= "https://zenodo.org/records/17432440?token=eyJhbGciOiJIUzUxMiIsImlhdCI6MTc2MTMxNzMyOSwiZXhwIjoxNzYxMzUwMzk5fQ.eyJpZCI6IjkwZmYzN2VkLWU4ODQtNDRkYi1iYzJkLTI4MzlmNzQwNGMzNSIsImRhdGEiOnt9LCJyYW5kb20iOiJlZjZjZGU4ZWQxODZiMmY3Mjc0NDBmYTlmMjJkNTc2ZiJ9.4Vir3SjrVgp6vL-1hzmuxXq-nGBkuapZ8t2wWAAtbzNxc7DcUJDNoECSoJoJjeeKEJyn8K5CqjGzhFPykhJhwg"

    from pathlib import Path
    current_dir = Path(__file__).resolve().parent
    # using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
    project_root = current_dir.parent.parent

    if output_folder is None:
        output_folder = f"{project_root}/data"
    else:
        # rewrite the raw seismic path
        yaml = YAML()
        yaml.preserve_quotes = True

        catchment_code = f"{project_root}/config/data_path.yaml"
        with open(catchment_code, "r") as f:
            config = yaml.load(f)

        config['glic_sac_dir'] = output_folder
        with open(catchment_code, "w") as f:
            yaml.dump(config, f)

        print(f"Update the <glic_sac_dir> in {catchment_code}")

    os.makedirs(output_folder, exist_ok=True)
    print(f"Raw seismic data was saved at:\n"
          f"{output_folder}")

    # down from Zenodo
    try:
        # compressed_type = "zip"
        # zenodo_url = f"https://zenodo.org/record/15020368/files/0seismic_feature.{compressed_type}"
        # output_folder = "/Users/qizhou/#python/#GitHub_saved/Flow-Bench/data"

        zenodo_downloader(zenodo_url, output_folder)
    except Exception as e:
        print("Please download it (zenodo_downloader) manually.")

    # down from FDSN
    df = pd.read_csv(f"{project_root}/data/event_catalog/Flow_Bench_Catalog_work.txt", header=0)

    arr = np.array(df)
    index = np.where((arr[:, 5] != "Private") &
                     (arr[:, 5] != "Zenodo"))

    fdsn_downloader(arr=arr[index], output_folder=output_folder, before=1, after=1)
    merge_stationxml(output_folder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sca_path", type=str, default="glic path", help="check the sac path")
    args = parser.parse_args()

    main(args.output_folder)


# # user case
# output_folder, continent, catchment = current_dir, "North_American", "Mount_Joffre"
# client_name, network, station, location, channel = "IRIS", "CN", "WSLR", "", "HHZ"
# start_time, end_time = "2019-05-13T13:00:00", "2019-05-16T17:00:00"
# before, after = 5, 5
# single_downloader(output_folder, continent, catchment,
#                   client_name, network, station, location, channel,
#                   start_time, end_time,
#                   before, after)
#
# output_folder = "/Users/qizhou/Desktop"
# merge_stationxml(output_folder)
