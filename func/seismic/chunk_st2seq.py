#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-06-19
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz-potsdam.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd
# Please do not distribute this code without the author's permission

import pytz
from datetime import datetime, timedelta, timezone

import numpy as np
import warnings

def chunk_data(data, data_start_time, data_sps, window_size, window_overlap):
    '''
    Chunk the data into chunks of size window_size

    Args:
        data: 1D data-array,
        data_start_time: str, format as "%Y-%m-%dT%H:%M:%S"
        data_sps: int or float, data sampling rate
        window_size: int, unit by second,
        window_overlap: float, overlap between windows

    Returns:
        t_value: 1D array-like time stamps
        t_str: 1D array-like time str
        chunk_x: 1D array-like chunk data
    '''
    x_seq_length = int(data_sps * window_size)  # samples per window
    step = int(x_seq_length * (1 - window_overlap))  # step size

    n_windows = (len(data) - x_seq_length) // step + 1
    last_idx = n_windows * step + x_seq_length - step

    # warn if last window is too short
    if last_idx < len(data):
        warnings.warn(f"\nLast window is smaller than window_size. \n"
                      f"data size in last window: {len(data) - n_windows * step}\n"
                      f"data size in normal window:  {x_seq_length}")

    # use stride_tricks to generate overlapping windows
    shape = (n_windows, x_seq_length)
    strides = (data.strides[0] * step, data.strides[0])
    chunk_x = np.lib.stride_tricks.as_strided(data[:last_idx], shape=shape, strides=strides)

    # generate timestamps
    date_start_time = datetime.strptime(data_start_time, "%Y-%m-%dT%H:%M:%S")
    timestamps = np.array([date_start_time + timedelta(seconds=i / data_sps) for i in range(len(data))])
    timestamps = np.array([(ts - datetime(1970, 1, 1)).total_seconds() for ts in timestamps])

    # the start time of the segement
    t_value = timestamps[::step][:n_windows]
    t_str = [datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() for ts in t_value]

    return t_value, t_str, chunk_x
