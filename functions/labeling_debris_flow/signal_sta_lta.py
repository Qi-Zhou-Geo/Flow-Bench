#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2024-02-23
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd
# Please do not distribute this code without the author's permission

import numpy as np
from scipy.signal import hilbert

from datetime import datetime, timedelta
from obspy import read, Trace, Stream
from obspy.core import UTCDateTime  # default is UTC+0 time zone
from obspy.signal.trigger import classic_sta_lta, trigger_onset

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
from functions.seismic.generate_seismic_trace import create_trace


def sta_lta_timing(st, short_window, long_window, ratio_on, ratio_off):

    tr = stream_to_trace(st=st)

    sampling_rate = tr.stats.sampling_rate
    max_amp_t = tr.stats.starttime + np.argmax(tr.data) / sampling_rate

    n_short = int(short_window * sampling_rate)
    n_long = int(long_window * sampling_rate)

    # forward STA/LTA (for start time)
    # only select the start time (time_on)
    cft = classic_sta_lta(tr.data, nsta=n_short, nlta=n_long)
    triggers = trigger_onset(cft, ratio_on, ratio_off)

    time_on = []
    for on, _ in triggers:
        t_on = tr.stats.starttime + on / sampling_rate
        # make sure the start time is earlier than max amplitude time
        if t_on <= max_amp_t:
            time_on.append(t_on.strftime("%Y-%m-%dT%H:%M:%S"))

    # backward STA/LTA (for end time)
    tr_rev = tr.copy()
    tr_rev.data = tr_rev.data[::-1]

    cft_rev = classic_sta_lta(tr_rev.data, nsta=n_short, nlta=n_long)
    # Note: the backward methods only focus on the event end time,
    # the ratio off was used as "ratio_on"
    triggers_rev = trigger_onset(cft_rev, ratio_off, ratio_off)

    npts = tr.stats.npts
    time_off = []

    for on_rev, _ in triggers_rev:
        # reversed start measured from END of original
        end_sample = npts - on_rev
        t_end = tr.stats.starttime + end_sample / sampling_rate

        # make sure the end time is later than max amplitude time,
        if t_end > max_amp_t:
            time_off.append(t_end.strftime("%Y-%m-%dT%H:%M:%S"))

    # create the STA/LTA ratio trace
    st_cft_on = create_trace(data=cft,
                             start_time=tr.stats.starttime,
                             data_sampling_rate=tr.stats.sampling_rate,
                             ref_st=tr)

    cft_rev = cft_rev[::-1] # rever back
    st_cft_off = create_trace(data=cft_rev,
                             start_time=tr.stats.starttime,
                             data_sampling_rate=tr.stats.sampling_rate,
                             ref_st=tr)

    return st_cft_on, st_cft_off, time_on, time_off
