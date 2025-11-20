#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou and Sibashish Dash, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import os
import array
import pickle

import numpy as np
import pandas as pd

from datetime import datetime

from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform

from dtaidistance import dtw
from dtaidistance import dtw_visualisation as dtwvis

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
import seaborn as sns

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path

current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys

sys.path.append(str(project_root))
# </editor-fold>

# import the custom functions
from functions.dynamic_time_warping.dwt_warping import *
from functions.dynamic_time_warping.plot_dwt_warping_func import plot_elbow_silhouette



#QZ ---------------- set parameters ---------------- #QZ
event_seperator = 66
denoise_time_window_size = 10  # denoise time window, second
time_type = "STA/LTA" # "extened_time" #
window_overlap = 0
denoising_method = "RMS"

#QZ ---------------- load and process the data ---------------- #QZ
cached_file = Path(f"{project_root}/pipeline/cal_dwt_matrix/traces_list.pkl")
# this will save time
if cached_file.exists():
    with open(cached_file, "rb") as f:
        data = pickle.load(f)
        traces_list = data["traces_list"]
        unique_id_list = data["unique_id_list"]
else:
    traces_list, unique_id_list = load_and_smooth_all_traces(window_size=denoise_time_window_size,
                                                             window_overlap=window_overlap,
                                                             denoising_method=denoising_method,
                                                             time_type=time_type)
    with open(cached_file, "wb") as f:
        pickle.dump({"traces_list": traces_list,
                     "unique_id_list": unique_id_list}, f)


# seperate the trace and the unique ID
ILL_traces = traces_list[:event_seperator]
non_ILL_traces = traces_list[event_seperator:]

unique_id_list_ILL = unique_id_list[:event_seperator]
unique_id_list_nonILL = unique_id_list[event_seperator:]

# create a dict for later useage
loaded_traces = {"ILL_traces":ILL_traces, "non_ILL_traces":non_ILL_traces}
laoded_traces_id = {"ILL_traces":unique_id_list_ILL, "non_ILL_traces":unique_id_list_nonILL}



# <editor-fold desc="cluster the ILL events">
# extract the tr's amplitude
obj_trace = "ILL_traces"
traces_amp = []
traces_amp_index = []
for idx, tr in enumerate(loaded_traces.get(obj_trace)):
    amp = tr.data

    amp = min_max_normalize(amp)
    amp_index = generate_amp_index(amp)

    traces_amp.append(amp)
    traces_amp_index.append(amp_index)

    print(f"{idx+1}, {tr.stats.network}, {tr.stats.station}, {tr.stats.channel}, {tr.stats.starttime}, {tr.stats.endtime}")

# calculate the dwt distance in this list
distance_matrix = calculate_dwt_matrix(traces_amp)
dm = distance_matrix.copy()
np.fill_diagonal(dm, np.nan)

min_dist    = np.nanmin(dm)
median_dist = np.nanmedian(dm)
max_dist    = np.nanmax(dm)
print(f"min_dist, median_dist, max_dist "
      f"{min_dist: .2f}, {median_dist: .2f}, {max_dist: .2f}")



linkage_method = "ward" # "complete" # "average" # "ward"-> #'complete'
condensed_matrix = squareform(distance_matrix)
linked = linkage(condensed_matrix, method=linkage_method)
np.save(f"{project_root}/pipeline/cal_dwt_matrix/linked.npy", linked)


# check how many clusters should be used
plot_elbow_silhouette(linked, distance_matrix)


# after run <plot_silhouette_score>, choose 2
num_cluster = 3
cluster_labels = fcluster(Z=linked, t=num_cluster, criterion='maxclust')

np.savez(f"{project_root}/pipeline/cal_dwt_matrix/traces_amp_{obj_trace}.npz",
         denoise_time_window_size=denoise_time_window_size,
         unique_id_list=unique_id_list_ILL,
         traces_amp_index=np.array(traces_amp_index, dtype=object),
         traces_amp=np.array(traces_amp, dtype=object),
         traces_cluster_labels=np.array(cluster_labels),
         time_processed=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
# </editor-fold>


# <editor-fold desc="cluster the non-ILL events">
obj_trace = "ILL_traces"
traces_amp = []
traces_amp_index = []
for idx, tr in enumerate(loaded_traces.get(obj_trace)):
    amp = tr.data

    amp = min_max_normalize(amp)
    amp_index = generate_amp_index(amp)

    traces_amp.append(amp)
    traces_amp_index.append(amp_index)

    print(f"{idx+1}, {tr.stats.network}, {tr.stats.station}, {tr.stats.channel}, {tr.stats.starttime}, {tr.stats.endtime}")

template_labels = cluster_labels # this follows the previous step
template_traces = traces_amp
assert len(template_labels) == len(traces_amp), (f"Error!\n "
                                                 f"len(template_labels) != len(traces_amp),\n "
                                                 f"{len(template_labels)} != {len(traces_amp)}")


# extract the tr's amplitude
obj_trace = "non_ILL_traces"
traces_amp = []
traces_amp_index = []
for idx, tr in enumerate(loaded_traces.get(obj_trace)):
    amp = tr.data

    amp = min_max_normalize(amp)
    amp_index = generate_amp_index(amp)

    traces_amp.append(amp)
    traces_amp_index.append(amp_index)

    print(f"{idx+event_seperator+1}, {tr.stats.network}, {tr.stats.station}, {tr.stats.channel}, {tr.stats.starttime}, {tr.stats.endtime}")


# start the searching
cluster_labels_nonILL = []
cluster_labels_nonILL_stats = []
nonILL_fitted_all_dwt_d = []
for idx, target_trace in enumerate(traces_amp):

    temp_target_label, temp_dwt_matrix = cluster_target(target_trace, template_labels, template_traces)


    # find the best label based the min DWT
    best_cluster = min(
        temp_target_label,
        key=lambda k: temp_target_label[k]["min"]
        # key=lambda k: temp_target_label[k]["mean"]
    )

    # find the best stats
    best_stats = temp_target_label[best_cluster]
    mean_dwt = best_stats['mean']
    q5, q95 = best_stats['q5'], best_stats['q95']
    min_dwt = best_stats['min']
    num_ref_traces = best_stats['num_ref_traces']

    cluster_labels_nonILL.append(best_cluster)
    cluster_labels_nonILL_stats.append(best_stats)
    nonILL_fitted_all_dwt_d.append(temp_dwt_matrix )

    print(f"{idx + 1 + event_seperator}, Cluster: {best_cluster}, Stats: {q5}, {q95}, {mean_dwt}, {min_dwt}")

# save as npz
np.savez(f"{project_root}/pipeline/cal_dwt_matrix/traces_amp_{obj_trace}.npz",
         denoise_time_window_size=denoise_time_window_size,
         unique_id_list=unique_id_list_nonILL,
         traces_amp_index=np.array(traces_amp_index, dtype=object),
         traces_amp=np.array(traces_amp, dtype=object),
         traces_cluster_labels=np.array(cluster_labels_nonILL),
         time_processed=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))


cluster_labels_nonILL = []
nonILL_fitted_all_dwt_d = []
for idx, target_trace in enumerate(traces_amp):

    best_cluster, temp_dwt_matrix = cluster_target_statis(target_trace, template_labels, template_traces)

    cluster_labels_nonILL.append(best_cluster)
    nonILL_fitted_all_dwt_d.append(temp_dwt_matrix)

np.savez(f"{project_root}/pipeline/cal_dwt_matrix/traces_dwt_statistics.npz",
         denoise_time_window_size=denoise_time_window_size,
         unique_id_list=unique_id_list_nonILL,
         traces_cluster_labels=np.array(cluster_labels_nonILL),
         nonILL_fitted_all_dwt_d=np.array(nonILL_fitted_all_dwt_d),
         time_processed=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
# </editor-fold>

