#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-16T18:23:03
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
from scipy.signal import hilbert


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
from func.seismic.generate_seismic_trace import create_trace
from func.seismic.chunk_st2seq import chunk_data


def amp_to_envelop(signal):
    """
    calculate the envelop of a seismic signal

    Args:
       signal: 1D numpy array, time series seismic signal

    Returns:
        amplitude_envelope: 1D numpy array,

    """

    analytic_signal = hilbert(signal)
    amplitude_envelope = np.abs(analytic_signal)

    return amplitude_envelope


def denoising(chunk_x, denoising_method, row_or_column="row"):
    """
    Apply a denoising/statistical summary method to 2D chunked data.

    Args:
        chunk_x: 2D numpy array.
            Each row is one time window, and each column is one sample inside that window.

        denoising_method: str.
            Method used to summarize each window. Options: "RMS" or "IQR".

        row_or_column: str.
            "row" summarizes each row/window and returns one value per window.
            "column" summarizes each column/sample position and returns one value per sample position.

    Returns:
        x_value: 1D numpy array.
            If row_or_column == "row", shape is (chunk_x.shape[0],).
            If row_or_column == "column", shape is (chunk_x.shape[1],).
    """

    if row_or_column == "row":
        axis = 1
    elif row_or_column == "column":
        axis = 0
    else:
        raise ValueError(f"row_or_column must be 'row' or 'column', got {row_or_column}")

    # denoise the data
    if denoising_method == "RMS":
        x_value = np.sqrt(np.mean(chunk_x**2, axis=axis))
    elif denoising_method == "IQR":
        x_q75 = np.percentile(chunk_x, 75, axis=axis)
        x_q25 = np.percentile(chunk_x, 25, axis=axis)
        x_value = x_q75 - x_q25
    else:
        raise ValueError(f"denoising_method must be 'RMS' or 'IQR', got {denoising_method}")

    return x_value


def denoise_st(st, window_size, window_overlap, denoising_method, fmt="%Y-%m-%dT%H:%M:%S"):
    """
    Convert a high-sampling-rate seismic stream into a lower-sampling-rate denoised time series using window-based RMS or IQR.
    """

    # (1) obspy stream >> trace
    tr = stream_to_trace(st)
    stats, data = tr.stats, tr.data  # type: ignore

    # (2) preparea the data
    seismic_data = amp_to_envelop(signal=data)  # return as 1D array
    sampling_rate = stats.sampling_rate
    start_time = stats.starttime.strftime(fmt)

    # (3) chunk and denoise the data
    t_value, t_str, chunk_x = chunk_data(
        data=seismic_data,
        data_start_time=start_time,
        data_sps=sampling_rate,
        window_size=window_size,
        window_overlap=window_overlap,
        fmt=fmt,
    )

    x_value = denoising(
        chunk_x=chunk_x,
        denoising_method=denoising_method,
        row_or_column="row",
    )

    # (4) warp the denoised data as stream
    low_sampling_rate = 1 / (window_size * (1 - window_overlap))
    denoised_st = create_trace(
        data=x_value,
        start_time=t_str[0],
        data_sampling_rate=low_sampling_rate,
        ref_st=tr,
    )

    return low_sampling_rate, denoised_st
