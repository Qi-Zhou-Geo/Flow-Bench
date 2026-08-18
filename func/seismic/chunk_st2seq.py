#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-16T18:08:19
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
from obspy import UTCDateTime


def chunk_data(data, data_start_time, data_sps, window_size, window_overlap, fmt="%Y-%m-%dT%H:%M:%S"):
    """
    Chunk 1D data into overlapping windows.

    Args:
        data: 1D data-array,
        data_start_time: str, format as "%Y-%m-%dT%H:%M:%S"
        data_sps: int or float, data  sampling rate in Hz
        window_size: int or float, window length in seconds
        window_overlap: float, fraction overlap between windows, e.g. 0.5
        fmt: str, output time-string format

    Returns:
        t_value: list of float timestamps for window start times
        t_str: list of formatted UTC time strings for window start times
        chunk_x: 2D array, shape = (n_windows, samples_per_window)
    """

    data = np.asarray(data)

    if data.ndim != 1:
        raise ValueError("data must be 1D")

    if not (0 <= window_overlap < 1):
        raise ValueError("window_overlap must satisfy 0 <= window_overlap < 1\n\n")

    x_seq_length = int(data_sps * window_size)  # samples per window
    step = int(x_seq_length * (1 - window_overlap))  # step size

    n_windows = (len(data) - x_seq_length) // step + 1
    last_idx = n_windows * step + x_seq_length - step

    # warn if last window is too short
    if len(data) < x_seq_length:
        raise ValueError(
            f"Data is shorter than one full window.\ndata size: {len(data)}, window size: {x_seq_length}\n\n"
        )

    starts = np.arange(0, len(data) - x_seq_length + 1, step)
    n_windows = len(starts)
    tail_samples = len(data) - (starts[-1] + x_seq_length)

    if tail_samples > 0:
        print(
            f"Unused tail after last full window is shorter than window_size.\n"
            f"unused tail samples: {tail_samples}\n"
            f"normal window samples: {x_seq_length}\n\n"
        )

    # use stride_tricks to generate overlapping windows
    shape = (n_windows, x_seq_length)
    strides = (data.strides[0] * step, data.strides[0])
    chunk_x = np.lib.stride_tricks.as_strided(data[:last_idx], shape=shape, strides=strides)

    # generate timestamps
    date_start_time = UTCDateTime(data_start_time)
    t_float = []
    t_str = []
    for start in starts:
        window_start_time = date_start_time + start / data_sps

        t_float.append(float(window_start_time))
        t_str.append(window_start_time.strftime(fmt))

    return t_float, t_str, chunk_x
