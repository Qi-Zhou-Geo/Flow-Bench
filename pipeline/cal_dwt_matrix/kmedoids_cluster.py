#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-14T20:44:50
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import pickle
import kmedoids
import numpy as np

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
from func.dwt.dwt_box import box_plot_dtw_distance_by_cluster
from func.dwt.kmedoids_tool import assign_non_ILL_to_kmedoids, calculate_medoid_thresholds
from func.dwt.dwt_box import plot_clustered_traces


fmt = "%Y-%m-%dT%H:%M:%S"
num_cluster = 3
unknown_cluster = 4
unknown_percentile = 90
unknown_factor = 1.5


# region
# Step 1: Load existing DTW results
ILL_data_path = Path(project_root) / "pipeline/cal_dwt_matrix/ILL_dwt.npz"
non_ILL_data_path = Path(project_root) / "pipeline/cal_dwt_matrix/non_ILL_dwt.npz"

ILL_data = np.load(ILL_data_path, allow_pickle=True)
non_ILL_data = np.load(non_ILL_data_path, allow_pickle=True)

distance_matrix = np.asarray(ILL_data["distance_matrix"], dtype=np.float64)
ILL_traces_amp = ILL_data["ILL_traces_amp"]
ILL_traces_meta = ILL_data["ILL_traces_meta"]

non_ILL_distance_matrix = np.asarray(non_ILL_data["non_ILL_distance_matrix"], dtype=np.float64)
non_ILL_traces_amp = non_ILL_data["non_ILL_traces_amp"]
non_ILL_traces_meta = non_ILL_data["non_ILL_traces_meta"]
# endregion


# region
# Step 2: K-medoids clustering for Illgraben events
result = kmedoids.fasterpam(distance_matrix, num_cluster, max_iter=1000, init="build", random_state=0)

ILL_cluster_labels = result.labels + 1  # from 1 to num_cluster
medoid_indices = result.medoids
medoid_meta = np.asarray(ILL_traces_meta, dtype=object)[medoid_indices]

print("K-medoids for Illgraben events")
print("Medoid event IDs:", medoid_indices)  # the event ID from 0
print("Medoid event names:", medoid_meta)
print("Cluster sizes:", np.bincount(ILL_cluster_labels)[1:])


thresholds = calculate_medoid_thresholds(
    distance_matrix=distance_matrix,
    cluster_labels=ILL_cluster_labels,
    medoid_indices=medoid_indices,
    percentile=unknown_percentile,
    factor=unknown_factor,
)

print("Cluster-specific unknown thresholds:")
for cluster, threshold in thresholds.items():
    print(f"Cluster {cluster}: {threshold:.4f}")


plot_clustered_traces(
    traces_amp=ILL_traces_amp,
    traces_meta=ILL_traces_meta,
    traces_cluster_labels=ILL_cluster_labels,
    max_clusters=5,
    name="DTW_kmedoids_ILL_traces",
    medoid_indices=medoid_indices,
)

box_plot_dtw_distance_by_cluster(
    distance_matrix=distance_matrix,
    cluster_labels=ILL_cluster_labels,
    save_path=f"{project_root}/plots/fig3/ILL_DTW_kmedoids_distance_boxplot.png",
    start_index=1,
)
# endregion


# region
# Step 3: Assign non-Illgraben events to Illgraben k-medoids
non_ILL_cluster_labels = []
non_ILL_statistic = []

for event_id, distance_row in enumerate(non_ILL_distance_matrix):
    cluster, output = assign_non_ILL_to_kmedoids(
        distances_to_all_templates=distance_row,
        medoid_indices=medoid_indices,
        thresholds=thresholds,
        unknown_cluster=unknown_cluster,
    )

    non_ILL_cluster_labels.append(cluster)
    non_ILL_statistic.append(output)

    output_name = non_ILL_traces_meta[event_id]
    print(
        f"{output_name}\n",
        f"assigned_cluster >> {cluster}\n",
        f"nearest_ill_cluster >> {output['nearest_ill_cluster']}\n",
        f"nearest_medoid_event_id >> {output['nearest_medoid_event_id']:03d}\n",
        f"nearest_medoid_distance >> {output['nearest_medoid_distance']: .4f}\n",
        f"threshold >> {output['threshold']: .4f}\n\n",
    )

non_ILL_cluster_labels = np.asarray(non_ILL_cluster_labels)

plot_clustered_traces(
    traces_amp=non_ILL_traces_amp,
    traces_meta=non_ILL_traces_meta,
    traces_cluster_labels=non_ILL_cluster_labels,
    max_clusters=5,
    name="DTW_kmedoids_non_ILL_traces",
)

box_plot_dtw_distance_by_cluster(
    distance_matrix=non_ILL_distance_matrix,
    cluster_labels=non_ILL_cluster_labels,
    save_path=f"{project_root}/plots/fig3/non_ILL_DTW_kmedoids_distance_boxplot.png",
    start_index=64,
    xlim=(0, 6),
)
# endregion

all_labels_path = Path(project_root) / "pipeline/cal_dwt_matrix/all_labels.npz"
np.savez_compressed(
    all_labels_path,
    ILL_cluster_labels=ILL_cluster_labels,
    non_ILL_cluster_labels=non_ILL_cluster_labels,
)


# save to local
all_labels = np.append(ILL_cluster_labels, non_ILL_cluster_labels)
print(all_labels.shape)


version = "v2dot1dot5"
fmt = "%Y-%m-%dT%H:%M:%S"
identifier = build_identifier(version=version, fmt=fmt)
dtw_dict = {}
for event_id in range(59, 141):
    temp = identifier[event_id]
    label = all_labels[event_id]
    dtw_dict[event_id] = [temp, label]

dtw_label_path = Path(project_root) / "data/cache/dtw_label.pkl"
with open(dtw_label_path, "wb") as f:
    pickle.dump(dtw_dict, f)

# with open(dtw_label_path, "rb") as f:
#     dtw_dict = pickle.load(f)
