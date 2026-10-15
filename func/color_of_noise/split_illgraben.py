#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-04T18:01:25
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz-potsdam.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd

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


def split_gfz_wsl_event(version="v2dot1dot5"):

    # load the meta
    fb = FlowBench(version=version)
    seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)

    # GFZ marker timestamps
    # this event not in WSL event catalog, it may stoped before reach to CD29
    gfz_marker = [
        "2014-04-26T22:30:00",
        "2014-04-29T09:00:00",
        "2014-04-30T11:00:00",
        "2014-05-02T03:00:00",
        "2014-05-23T04:00:00",
        "2014-05-27T05:30:00",
        "2014-06-19T14:00:00",
        "2014-06-23T17:30:00",
        "2014-08-02T17:30:00",
        "2014-08-08T18:30:00",
        "2014-08-11T00:00:00",
        "2014-08-13T03:00:00",
    ]

    # convert time
    gfz_marker_day = [UTCDateTime(dt).julday for dt in gfz_marker]
    gfz_marker_year = [UTCDateTime(dt).year for dt in gfz_marker]

    gfz_event_id = []
    wsl_event_id = []
    for idx in range(len(event_meta)):
        catchment = seis_meta["seis_cat"][idx]
        event_start = UTCDateTime(event_meta["event_time_s"][idx])

        if catchment == "Illgraben":
            if event_start.year in gfz_marker_year and event_start.julday in gfz_marker_day:
                gfz_event_id.append(idx)
            else:
                wsl_event_id.append(idx)

    return gfz_event_id, wsl_event_id


def usage():
    gfz_event_id, wsl_event_id = split_gfz_wsl_event(version="v2dot1dot5")
