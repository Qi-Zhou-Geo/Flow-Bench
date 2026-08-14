#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-14T10:00:28
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np

from obspy import read, Trace, Stream
from obspy.core import UTCDateTime  # default is UTC+0 time zone
from obspy.signal.trigger import classic_sta_lta

from scipy.ndimage import median_filter

import matplotlib.pyplot as plt


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
from func.seismic.plot_obspy_st import time_series_plot


def min_max_normalize(data):
    
    if data.ndim >= 2:
        raise ValueError(
            f"This function does not support arrays with ndim >= 2. "
            f"Got data.ndim={data.ndim}."
        )
    
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


def get_event_windows(event_mask, sps, starttime=None):
    
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

        windows.append({
            "start_idx": start_idx,
            "end_idx": end_idx,
            "start_time": start_time,
            "end_time": end_time,
            "duration_sec": duration_sec,
        })

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
            print(f"Warning! Event {event_id} is too short:\n"
                  f'{event_timing[f"{event_id}_start_time"]}, {event_timing[f"{event_id}_end_time"]}\n'
                  f"duration={duration:.2f} s, minimum={min_event_duration} s\n\n")
            continue

        # separation from previous event
        if previous_end is not None:
            separation = start - previous_end
            if separation < min_event_separation:
                print(f"Warning! Events {event_id} are too close:\n"
                    f'{event_timing[f"{event_id}_start_time"]}, {event_timing[f"{event_id}_end_time"]}\n'
                    f"separation={separation:.2f} s, minimum={min_event_separation} s\n\n")
                continue
            
        # update
        previous_end = end
        
        filtered_event_timing[start_key] = event_timing[start_key]
        filtered_event_timing[end_key] = event_timing[end_key]


    return filtered_event_timing


def forward_backward_sta_lta(st,
                             sta, lta, 
                             smooth_sec, 
                             thr_on, thr_off,
                             
                             min_event_duration=600,
                             min_event_separation=1800,
                             format_t_str="%Y-%m-%dT%H:%M:%S"):
    
    # (1) extract the data
    data = st[0].data
    starttime = st[0].stats.starttime
    sps = st[0].stats.sampling_rate
    
    
    # (2) forward STA/LTA for start time
    forward = classic_sta_lta(a=data, nsta=int(sta * sps), nlta=int(lta * sps))
    forward = min_max_normalize(data=forward)
    smooth_forward = median_filter(input=forward, size=int(smooth_sec * sps))
    
    smooth_forward_st = create_trace(data=smooth_forward, 
                                     start_time=starttime, 
                                     data_sampling_rate=sps, ref_st=st)
    
    # build the event yes-no mask
    forward_mask = hysteresis_mask(score=smooth_forward, thr_on=thr_on, thr_off=thr_off)
    forward_windows = get_event_windows(event_mask=forward_mask, sps=sps, starttime=starttime)



    # (3) backward STA/LTA for end time
    inverse_data = data[::-1]
    backward = classic_sta_lta(a=inverse_data, nsta=int(sta * sps), nlta=int(lta * sps))
    backward = min_max_normalize(data=backward)
    smooth_backward = median_filter(input=backward, size=int(smooth_sec * sps))
    inverse_smooth_backward = smooth_backward[::-1]
    
    inverse_smooth_backward_st = create_trace(data=inverse_smooth_backward, 
                                              start_time=starttime, 
                                              data_sampling_rate=sps, ref_st=st)
    
    # build the event yes-no mask
    backward_mask = hysteresis_mask(score=inverse_smooth_backward, thr_on=thr_on, thr_off=thr_off)
    backward_windows = get_event_windows(event_mask=backward_mask, sps=sps, starttime=starttime)
    
    

    # (4) check the 
    event_timing = {}
    if len(forward_windows) == len(backward_windows):
        # loop add all timing
        for i, (start_t, end_t) in enumerate(zip(forward_windows, backward_windows)):
            event_timing[f"{i:03d}_start_time"] = UTCDateTime(start_t['start_time']).strftime(format_t_str)
            event_timing[f"{i:03d}_end_time"] = UTCDateTime(end_t['end_time']).strftime(format_t_str)
            
    else:
        raise ValueError(f"len(forward_windows) != len(backward_windows)")
    
    event_timing = check_event_timing(event_timing=event_timing, min_event_duration=min_event_duration, min_event_separation=min_event_separation)
    
    
    
    # (5) prepare the results
    output = {
            "forward": forward,
            "smooth_forward_st": smooth_forward_st,
            
            "backward": backward,
            "inverse_smooth_backward_st": inverse_smooth_backward_st,
            
            "event_timing": event_timing
        }
    
    return output


def plot_sta_lta(st_file_list, 
                 time_markers,
                 time_markers_label,
                 f_min, f_max,
                 ratio_on, ratio_off,
                 output_path, output_name):
    
    fig, axes = time_series_plot(st_file_list, time_markers=time_markers, time_markers_label=time_markers_label)
    y_label = ["Amplitude\n[m/s]", "STA/LTA Ratio\n[forward]", "STA/LTA Ratio\n[backward]"]

    for idx, (ax, label) in enumerate(zip(axes, y_label)):
        ax.set_ylabel(f"{label}", fontweight='bold')

        if idx == 0:
            ax.set_title(label=f"f_min={f_min}, f_max={f_max}"
                               f"\nratio_on={ratio_on}, ratio_off={ratio_off}", fontsize=7, fontweight='bold')
        else:
            ax.axhline(y=ratio_on, color="red", ls="--", lw=1, alpha=0.5, zorder=5, label=f"ratio_on={ratio_on}")
            ax.axhline(y=ratio_off, color="green", ls="-", lw=1, alpha=0.5,  zorder=4, label=f"ratio_off={ratio_off}")
            ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0.3)
    
    png_path = Path(output_path) / output_name
    png_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(png_path, dpi=600, transparent=False)
    plt.close(fig)



def usage():
    st = read("/Users/qizhou/Desktop/cooked_2022-06-05.mseed")


    output = forward_backward_sta_lta(
        st=st,
        sta=180,
        lta=1800,
        smooth_sec=180,
        thr_on=0.2,
        thr_off=0.2,
    )



    
    st_file_list = Stream()
    st_file_list = st_file_list + st
    st_file_list = st_file_list + output['smooth_forward_st']
    st_file_list = st_file_list + output['inverse_smooth_backward_st']


    time_markers = []
    time_markers_label = []
    for key, value in output['event_timing'].items():
        
        if "start" in key:
            marker_temp = f"start: {value}"
        elif "end" in key:
            marker_temp = f"end: {value}"
        else:
            raise ValueError(f"Check the dict. No start or end time.")
        
        time_markers.append(value)
        time_markers_label.append(marker_temp)


    f_min, f_max = 1, 25
    ratio_on, ratio_off = 0.2, 0.2
    output_path, output_name = f"/Users/qizhou/Desktop", "test.png"
    plot_sta_lta(st_file_list, 
                time_markers, 
                time_markers_label, 
                f_min, f_max, 
                ratio_on, ratio_off, 
                output_path, output_name)
