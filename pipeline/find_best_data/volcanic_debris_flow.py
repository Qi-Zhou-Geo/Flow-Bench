#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-05T13:19:44
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import argparse

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion

from func.toolkit.xlsx_to_txt import xlsx2txt
from pipeline.find_best_data.workflow import check_nearby_station


def main(
    # meta for the debris flow events
    version,
    seis_cat,
    volcanic_meta,
    event_id,
    # meta for seaching the station
    continent="North American",
    radius_km=15,
    removed_network="1D",
    min_sps_hz=50,
    f_min=1,
    f_max=25,
):

    # extract the meta
    input_xlsx_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{version}.xlsx"
    output_txt_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{version}.txt"
    column_s, column_e = 15, 17
    df = xlsx2txt(input_xlsx_path, output_txt_path, column_s, column_e)

    starttime = df.iloc[event_id, 0]
    endtime = df.iloc[event_id, 1]
    seis_client, lat, lon = volcanic_meta.get(seis_cat)

    # search the available station with center (lat, lon)
    # this will plot (but not show it) the data and save the figure in the current folder
    st_cooked_all = check_nearby_station(
        # related to event
        starttime,
        endtime,
        # seismic meta
        continent,
        seis_cat,
        # search meta
        seis_client,
        lat,
        lon,
        min_sps_hz=min_sps_hz,
        radius_km=radius_km,
        removed_network=removed_network,
        # plot meta
        f_min=f_min,
        f_max=f_max,
        seis_response="xml",
        sensor_type="do-not-need-here",
    )

    return st_cooked_all


# in terminal
# python volcanic_debris_flow.py --version v2dot1dot5 --seis_cat Hood --event_id 103
# python volcanic_debris_flow.py --version v2dot1dot5 --seis_cat Shasta--event_id 122
if __name__ == "__main__":
    # receive the event id
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=str, default="v2dot1dot5")
    parser.add_argument("--seis_cat", type=str, default="Hood")
    parser.add_argument("--event_id", type=int, default=111)

    args = parser.parse_args()

    # prepare the parameters
    version = args.version
    seis_cat = args.seis_cat
    volcanic_meta = {
        # "seis_cat": (seis_client, lat, lon),
        "Helens": ("IRIS", 46.199347, -122.189968),
        "Hood": ("IRIS", 45.373198, -121.695682),
        "Rainier": ("IRIS", 46.852036, -121.758848),
        "Shasta": ("NCEDC", 41.409892, -122.194622),
    }
    event_id = args.event_id

    # run it
    st_cooked_all = main(
        # meta for the debris flow events
        version,
        seis_cat,
        volcanic_meta,
        event_id,
        # meta for seaching the station
        continent="North American",
        radius_km=15,
        removed_network="1D",
        min_sps_hz=50,
        f_min=1,
        f_max=25,
    )

    cache_dir = Path(project_root) / f"data/cache/{event_id:03d}_{seis_cat}_cooked_all.mseed"
    st_cooked_all.write(cache_dir, format="MSEED")
