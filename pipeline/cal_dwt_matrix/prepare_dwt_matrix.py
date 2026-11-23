#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-02T15:28:10
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
import matplotlib.pyplot as plt

from obspy import UTCDateTime

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
from func.flow_bench.unique_identifier import build_identifier
from func.dwt.dwt_matrix import min_max_normalize, calculate_dwt_matrix
from func.dwt.dwt_match import assign_dtw_cluster


# event related
version = "v2dot1dot5"
fmt = "%Y-%m-%dT%H:%M:%S"
event_seperator = 63  # total 63 Illgraben events
identifier = build_identifier(version=version, fmt=fmt)


# region Step 1
#
# (1) load all ILlgranen events
ILL_traces_amp = []
ILL_traces_meta = []
for event_id in np.arange(event_seperator):
    output_name = identifier[event_id]
    npz_path = Path(project_root) / f"data/cache/denoised_st/{output_name}.npz"

    data = np.load(npz_path)
    denoised_amp = data["denoised_st"]  # denoised amp by RMS with 10s window

    amp = min_max_normalize(denoised_amp)  # normalized from 0-1

    ILL_traces_amp.append(amp)
    ILL_traces_meta.append(output_name)

    print(f"Done: {output_name}\n")

# plot it to check the amp
first_event = ILL_traces_amp[0]
plt.plot(first_event)
plt.title("First Illgraben event")
plt.show()


# (2) calculate the dwt distance in this list
distance_matrix = calculate_dwt_matrix(ILL_traces_amp)
dm = distance_matrix.copy()
np.fill_diagonal(dm, np.nan)


# print
output_name = "All Illgraben event"
min_dist = np.min(dm)
mean_dist = np.mean(dm)
median_dist = np.median(dm)
max_dist = np.max(dm)
std_dist = np.std(dm, ddof=1)  # sample standard deviation
print(
    f"{output_name}\n",
    f"min_dist >> {min_dist: .4f}\n",
    f"mean_dist >> {mean_dist: .4f}\n",
    f"median_dist >> {median_dist: .4f}\n",
    f"max_dist >> {max_dist: .4f}\n\n",
)
# endregion


# region Step 2
#
np.savez(
    f"{project_root}/pipeline/cal_dwt_matrix/ILL_dwt.npz",
    ##
    distance_matrix=distance_matrix,
    ILL_traces_amp=np.array(ILL_traces_amp, dtype=object),
    ILL_traces_meta=np.array(ILL_traces_meta, dtype=object),
    ##
    time_processed=UTCDateTime.now().strftime(fmt),
)

# endregion


# region Step 3
non_ILL_traces_amp = []
non_ILL_traces_meta = []
for event_id in np.arange(event_seperator, len(identifier)):  # from first non-Ill event
    if event_id <= 140:
        output_name = identifier[event_id]
        npz_path = Path(project_root) / f"data/cache/denoised_st/{output_name}.npz"

        data = np.load(npz_path)
        denoised_amp = data["denoised_st"]  # denoised amp by RMS with 10s window

        amp = min_max_normalize(denoised_amp)  # normalized from 0-1
        non_ILL_traces_amp.append(amp)
        non_ILL_traces_meta.append(output_name)

        print(f"Done: {output_name}\n")
    else:
        # Illgraben 2021 data, QZ do not have the right to publish it now
        pass

    # plot it to check the amp
first_event = non_ILL_traces_amp[0]
plt.plot(first_event)
plt.title("First Non-Illgraben event")
plt.show()

# endregion


# region Step4
# start the searching
non_ILL_statistic = []
non_ILL_distance_matrix = []
# loop all non-Illgrabne event
for event_id, obs_trace in enumerate(non_ILL_traces_amp):
    # do the match
    output, distance_matrix = assign_dtw_cluster(
        obs_trace=obs_trace,
        template_traces=ILL_traces_amp,
    )

    non_ILL_statistic.append(output)
    non_ILL_distance_matrix.append(distance_matrix)

    # print
    output_name = identifier[event_id + event_seperator]
    min_dist = float(output["min_dist"])
    mean_dist = float(output["mean_dist"])
    median_dist = float(output["median_dist"])
    max_dist = float(output["max_dist"])

    print(
        f"{output_name}\n",
        f"min_dist >> {min_dist: .4f}\n",
        f"mean_dist >> {mean_dist: .4f}\n",
        f"median_dist >> {median_dist: .4f}\n",
        f"max_dist >> {max_dist: .4f}\n\n",
    )

non_ILL_distance_matrix = np.vstack(non_ILL_distance_matrix)

np.savez(
    f"{project_root}/pipeline/cal_dwt_matrix/non_ILL_dwt.npz",
    ##
    non_ILL_distance_matrix=non_ILL_distance_matrix,
    non_ILL_traces_amp=np.array(non_ILL_traces_amp, dtype=object),
    non_ILL_traces_meta=np.array(non_ILL_traces_meta, dtype=object),
    ##
    non_ILL_statistic=np.array(non_ILL_statistic, dtype=object),
    time_processed=UTCDateTime.now().strftime(fmt),
)

# endregion
