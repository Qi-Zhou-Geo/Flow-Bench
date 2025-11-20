#!/usr/bin/python
# -*- coding: UTF-8 -*-

#__modification time__ = 2024-02-23
#__author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
#__find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd
# Please do not distribute this code without the author's permission

import numpy as np

from obspy import read, Trace, Stream
from obspy.core import UTCDateTime # default is UTC+0 time zone

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>

# import the custom functions
from functions.seismic.st2tr import stream_to_trace

def create_trace(data, start_time, data_sampling_rate, ref_st=None):

    '''
    Create Obspy Trace and Stream
    Args:
        data: numpy 1D data-60s array, unit by m/s or other
        start_time: str, format by "%Y-%m-%dT%H:%M:%S"
        data_sampling_rate: int or float, unit by Hz
        ref_st: Trace or Stream, obspy Trace or Stream object

    Returns:
        st: obspy Stream object
    '''

    trace = Trace(data=data)
    trace.stats.sampling_rate = data_sampling_rate
    trace.stats.starttime = UTCDateTime(start_time)
    st = Stream([trace])

    if ref_st is None:
        pass
    else:
        # with reference stream
        ref_st = stream_to_trace(st=ref_st)

        # get the ref information
        st[0].stats.network = ref_st.stats.network
        st[0].stats.station = ref_st.stats.station
        st[0].stats.channel = ref_st.stats.channel

    return st
