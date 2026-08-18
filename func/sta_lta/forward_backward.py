#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-17T13:52:38
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np

from obspy import UTCDateTime
from obspy.signal.trigger import classic_sta_lta

from scipy.ndimage import median_filter


# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion

# import the custom func
from func.seismic.generate_seismic_trace import create_trace


def min_max_normalize(data):

    if data.ndim >= 2:
        raise ValueError(f"This function does not support arrays with ndim >= 2. Got data.ndim={data.ndim}.")

    min_data = np.min(data)
    max_data = np.max(data)

    norm_data = (data - min_data) / (max_data - min_data)

    return norm_data


def remove_short_events(mask, min_duration_samples):

    mask = mask.astype(bool)
    padded = np.r_[False, mask, False]
    changes = np.diff(padded.astype(int))

    starts = np.where(changes == 1)[0]
    ends = np.where(changes == -1)[0]

    clean_mask = np.zeros_like(mask, dtype=bool)

    for start, end in zip(starts, ends):
        if end - start >= min_duration_samples:
            clean_mask[start:end] = True

    return clean_mask


def get_event_windows(event_mask, sps, starttime, min_event_duration):

    event_mask = np.asarray(event_mask).astype(bool)

    padded = np.r_[False, event_mask, False]
    changes = np.diff(padded.astype(int))

    starts = np.where(changes == 1)[0]
    ends = np.where(changes == -1)[0]

    windows = []

    for start_idx, end_idx in zip(starts, ends):
        start_sec = start_idx / sps
        end_sec = end_idx / sps
        duration_sec = end_sec - start_sec

        if starttime is not None:
            start_time = starttime + start_sec
            end_time = starttime + end_sec
        else:
            start_time = start_sec
            end_time = end_sec

        if UTCDateTime(end_time) - UTCDateTime(start_time) >= min_event_duration:
            windows.append(
                {
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_sec": duration_sec,
                }
            )

    return windows


def hysteresis_mask(score, thr_on, thr_off):

    if thr_off > thr_on:
        raise ValueError("thr_off must be smaller than thr_on")

    mask = np.zeros_like(score, dtype=bool)
    active = False

    for i, value in enumerate(score):
        if not active and value >= thr_on:
            active = True
        elif active and value <= thr_off:
            active = False

        mask[i] = active

    return mask


def check_event_timing(event_timing, min_event_duration, min_event_separation):

    # extract the events ends
    event_ids = []
    for key in event_timing:
        if key.endswith("_start_time"):
            event_id = key.split("_")[0]
            event_ids.append(event_id)
    event_ids = sorted(event_ids)

    filtered_event_timing = {}
    previous_end = None
    for event_id in event_ids:
        start_key = f"{event_id}_start_time"
        end_key = f"{event_id}_end_time"

        start = UTCDateTime(event_timing[start_key])
        end = UTCDateTime(event_timing[end_key])

        # duration of current event
        duration = end - start
        if duration < min_event_duration:
            print(
                f"Warning! Event {event_id} is too short:\n"
                f"{event_timing[f'{event_id}_start_time']}, {event_timing[f'{event_id}_end_time']}\n"
                f"duration={duration:.2f} s, minimum={min_event_duration} s\n\n"
            )
            continue

        # separation from previous event
        if previous_end is not None:
            separation = start - previous_end
            if separation < min_event_separation:
                print(
                    f"Warning! Events {event_id} are too close:\n"
                    f"{event_timing[f'{event_id}_start_time']}, {event_timing[f'{event_id}_end_time']}\n"
                    f"separation={separation:.2f} s, minimum={min_event_separation} s\n\n"
                )
                continue

        # update
        previous_end = end

        filtered_event_timing[start_key] = event_timing[start_key]
        filtered_event_timing[end_key] = event_timing[end_key]

    return filtered_event_timing


def forward_backward_sta_lta(
    # obspy stream
    st,
    # STA-LTA
    sta,
    lta,
    thr_on,
    thr_off,
    # default params
    smooth_sec=None,
    min_event_duration=600,
    fmt="%Y-%m-%dT%H:%M:%S",
):

    # (1) extract the data
    st_copy = st.copy()
    data = st_copy[0].data
    starttime = st_copy[0].stats.starttime
    sps = st_copy[0].stats.sampling_rate

    # (2) forward STA/LTA for start time
    forward = classic_sta_lta(a=data, nsta=int(sta * sps), nlta=int(lta * sps))
    forward = min_max_normalize(data=forward)

    if smooth_sec is not None:
        smooth_forward = median_filter(input=forward, size=int(smooth_sec * sps))
    else:
        smooth_forward = forward

    smooth_forward_st = create_trace(data=smooth_forward, start_time=starttime, data_sampling_rate=sps, ref_st=st_copy)

    # build the event yes-no mask
    forward_mask = hysteresis_mask(score=smooth_forward, thr_on=thr_on, thr_off=thr_off)
    forward_windows = get_event_windows(
        event_mask=forward_mask, sps=sps, starttime=starttime, min_event_duration=min_event_duration
    )

    # (3) backward STA/LTA for end time
    inverse_data = data[::-1]
    backward = classic_sta_lta(a=inverse_data, nsta=int(sta * sps), nlta=int(lta * sps))
    backward = min_max_normalize(data=backward)

    if smooth_sec is not None:
        smooth_backward = median_filter(input=backward, size=int(smooth_sec * sps))
    else:
        smooth_backward = backward

    inverse_smooth_backward = smooth_backward[::-1]
    inverse_smooth_backward_st = create_trace(
        data=inverse_smooth_backward, start_time=starttime, data_sampling_rate=sps, ref_st=st_copy
    )

    # build the event yes-no mask
    backward_mask = hysteresis_mask(score=inverse_smooth_backward, thr_on=thr_on, thr_off=thr_off)
    backward_windows = get_event_windows(
        event_mask=backward_mask, sps=sps, starttime=starttime, min_event_duration=min_event_duration
    )

    # (4) check the
    event_timing = {}
    max_amp_t = UTCDateTime(starttime) + np.argmax(data) / sps  # maximum amplitude time

    for i, start_t in enumerate(forward_windows):
        delta_t = UTCDateTime(max_amp_t) - UTCDateTime(start_t["start_time"])
        if delta_t > 0:  # assume the start time is earlier than max amp time
            event_timing[f"{i:03d}_start_time"] = UTCDateTime(start_t["start_time"]).strftime(fmt)

    event_timing["max_amp_time"] = max_amp_t

    for i, end_t in enumerate(backward_windows):
        delta_t = UTCDateTime(max_amp_t) - UTCDateTime(end_t["end_time"])
        if delta_t < 0:  # assume the end time is later than max amp time
            event_timing[f"{i:03d}_end_time"] = UTCDateTime(end_t["end_time"]).strftime(fmt)

    # (5) prepare the results
    sta_lta_timing = {
        "forward": forward,
        "smooth_forward_st": smooth_forward_st,
        "backward": backward,
        "inverse_smooth_backward_st": inverse_smooth_backward_st,
        "event_timing": event_timing,
    }

    return sta_lta_timing
