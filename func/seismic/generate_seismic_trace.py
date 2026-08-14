#!/usr/bin/python
# -*- coding: UTF-8 -*-

#__modification time__ = Last modified: 2026-08-14T09:59:46
#__author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
#__find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd
# Please do not distribute this code without the author's permission

from obspy import Trace, Stream, UTCDateTime

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
        # get the ref information
        st[0].stats.network = ref_st[0].stats.network # type: ignore
        st[0].stats.station = ref_st[0].stats.station # type: ignore
        st[0].stats.channel = ref_st[0].stats.channel # type: ignore

    return st
