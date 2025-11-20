#!/usr/bin/python
# -*- coding: UTF-8 -*-

#__modification time__ = 2024-02-23
#__author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
#__find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd
# Please do not distribute this code without the author's permission

import numpy as np
from scipy.signal import hilbert

from datetime import datetime, timedelta
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
from functions.seismic.generate_seismic_trace import create_trace

def amp_to_envelop(signal):
    '''
    calculate the envelop of a seismic signal

    Args:
       signal: 1D numpy array, time series seismic signal

    Returns:
        amplitude_envelope: 1D numpy array,

    '''

    analytic_signal = hilbert(signal)
    amplitude_envelope = np.abs(analytic_signal)

    return amplitude_envelope

def denoising(chunk_x, denoising_method, row_or_column):
    '''
    provide different denoising methods

    Args:
        chunk_x: 2D numpy array, each row represents one time step
        denoising_method: str, denoising methods
        row_or_column: str, 0 denotes to column, 1 denotes row

    Returns:
        x_value: 1D numpy array,
        x_value.shape[0] should equal to chunk_x.shape[0]

    '''
    if row_or_column == "row":
        row_or_column = 1
    elif row_or_column == "column":
        row_or_column = 0
    else:
        print(f"check the row_or_column = {row_or_column}")

    if denoising_method == "RMS":
        x_value = np.sqrt(np.mean(chunk_x ** 2, axis=row_or_column))
    elif denoising_method == "IQR":
        x_q75 = np.percentile(chunk_x, 75, axis=row_or_column)
        x_q25 = np.percentile(chunk_x, 25, axis=row_or_column)
        x_value = x_q75 - x_q25
    else:
        print(f"check the denoising_method = {denoising_method}")

    return x_value

def st_denoising(st, window_size, window_overlap, denoising_method):
    '''
    receive high_sampling_rate seismic stream and use "RMS" or "IQR" to denosise the data in low_sampling_rate

    Args:
        seismic_data: 1D numpy array, unit by m/s
        start_time: str, start time of the seismic data, no physical unit
        sampling_rate: int, seismic data sampling rate, unit by Hz
        window_size: int, window size for praparing x data, unit by second
        window_overlap: float, overlap ratio for each time step, 0-> no overlap, 0.75->every step get 1/4 new data, no physical unit
        denoising_method: str, either "RMS" or "IQR", no physical unit

    Returns:
        t_value, x_value: 1D numpy array, smae as input physical unit
        low_sampling_rate (unit by Hz) = 1 / (window_size * (1 - window_overlap))
    '''

    tr = stream_to_trace(st)
    amplitude_envelope = amp_to_envelop(signal=tr.data)

    seismic_data = amplitude_envelope
    sampling_rate = tr.stats.sampling_rate
    start_time = tr.stats.starttime.strftime("%Y-%m-%dT%H:%M:%S")
    end_time = tr.stats.endtime.strftime("%Y-%m-%dT%H:%M:%S")


    x_seq_length = int(sampling_rate * window_size)  # x_seq_length unit by data point
    overlap_length = int(x_seq_length * (1 - window_overlap))  # unit by data point

    # prepare the float time stamps
    date_start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    date_end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
    tr.trim(UTCDateTime(date_start_time), UTCDateTime(date_end_time)) # make sure the data is start and end time

    timestamps = np.array([date_start_time + timedelta(seconds= i / sampling_rate) for i in range(len(seismic_data))])
    timestamps = np.array([(ts - datetime(1970, 1, 1)).total_seconds() for ts in timestamps])
    # you can use this to convert the float time back to string
    # datetime.utcfromtimestamp(t_value[1]).strftime('%Y-%m-%d %H:%M:%S.%f')

    # prepare a 2D data numpy array
    if window_overlap != 0:  # for overlap window
        chunk_t = np.lib.stride_tricks.sliding_window_view(timestamps, x_seq_length)[::overlap_length]
        chunk_x = np.lib.stride_tricks.sliding_window_view(seismic_data, x_seq_length)[::overlap_length]
    else:
        num_windows = len(seismic_data) // x_seq_length
        chunk_t = timestamps[:num_windows * x_seq_length].reshape(-1, x_seq_length)
        chunk_x = seismic_data[:num_windows * x_seq_length].reshape(-1, x_seq_length)

    t_value = chunk_t[:, 0]
    x_value = denoising(chunk_x=chunk_x, denoising_method=denoising_method, row_or_column="row")
    low_sampling_rate = 1 / (window_size * (1 - window_overlap))

    denoised_st = create_trace(data=x_value,
                               start_time=start_time,
                               data_sampling_rate= low_sampling_rate,
                               ref_st=tr)

    return t_value, x_value, low_sampling_rate, denoised_st

