#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-04T15:10:56
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

from obspy import Trace, Stream, UTCDateTime


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
from func.seismic.st2tr import stream_to_trace


def create_trace(data, start_time, data_sampling_rate, ref_st=None):
    """
    Create Obspy Trace and Stream.

    Args:
        data: 1D numpy array, unit by m/s or other
        start_time: str, format by "%Y-%m-%dT%H:%M:%S"
        data_sampling_rate: int or float, unit by Hz
        ref_st: Trace or Stream, obspy Trace or Stream object

    Returns:
        st: obspy Stream object
    """

    trace = Trace(data=data)
    trace.stats.sampling_rate = data_sampling_rate
    trace.stats.starttime = UTCDateTime(start_time)

    if ref_st is not None:
        ref_tr = stream_to_trace(ref_st)

        stats = ref_tr.stats  # type: ignore
        trace.stats.network = stats.network
        trace.stats.station = stats.station
        trace.stats.channel = stats.channel

    st = Stream([trace])

    return st
