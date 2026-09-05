#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-04T18:06:41
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import pandas as pd
from obspy import UTCDateTime

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
from func.flow_bench.FlowBench import FlowBench


def build_identifier(version="v2dot1dot5", fmt="%Y-%m-%dT%H:%M:%S"):

    # load the meta
    fb = FlowBench(version=version)
    seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)

    identifier = {}
    for event_id in range(len(seis_meta)):
        seis_row = seis_meta.iloc[event_id]
        event_row = event_meta.iloc[event_id]

        starttime = UTCDateTime(event_row["event_time_s"]).strftime(fmt)
        endtime = UTCDateTime(event_row["event_time_e"]).strftime(fmt)

        seis_location = seis_row["seis_location"]
        if pd.isna(seis_location) is True:
            seis_location = ""

        temp = (
            f"{event_id:03d}-"
            f"{seis_row['seis_network']}-"
            f"{seis_row['seis_station']}-"
            f"{seis_location}-"
            f"{seis_row['seis_channel']}-"
            f"{starttime}-"
            f"{endtime}"
        )
        identifier[event_id] = temp

    return identifier


def usage():
    identifier = build_identifier(version="v2dot1dot5", fmt="%Y%m%dT%H%M%S")
