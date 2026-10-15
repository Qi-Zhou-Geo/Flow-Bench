#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-11T18:08:51
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

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


def calculate_medoid_thresholds(distance_matrix, cluster_labels, medoid_indices, percentile=95, factor=1.0):

    distance_matrix = np.asarray(distance_matrix, dtype=float)  # 2D dtw matrix
    cluster_labels = np.asarray(cluster_labels)  # 1D event label

    thresholds = {}

    for cluster_id, medoid_idx in enumerate(medoid_indices, start=1):
        cluster_idx = np.where(cluster_labels == cluster_id)[0]
        distances_to_medoid = distance_matrix[cluster_idx, medoid_idx]
        thresholds[cluster_id] = float(np.percentile(distances_to_medoid, percentile) * factor)

    return thresholds


def assign_non_ILL_to_kmedoids(
    distances_to_all_templates,
    medoid_indices,
    thresholds,
    unknown_cluster=4,
):
    distances_to_all_templates = np.asarray(distances_to_all_templates, dtype=float)

    distances_to_medoids = distances_to_all_templates[medoid_indices]
    nearest_medoid_position = int(np.argmin(distances_to_medoids))
    nearest_cluster = nearest_medoid_position + 1
    nearest_distance = float(distances_to_medoids[nearest_medoid_position])
    threshold = float(thresholds[nearest_cluster])

    if nearest_distance > threshold:
        assigned_cluster = unknown_cluster
    else:
        assigned_cluster = nearest_cluster

    output = {
        "assigned_cluster": int(assigned_cluster),
        "nearest_ill_cluster": int(nearest_cluster),
        "nearest_medoid_index": int(medoid_indices[nearest_medoid_position]),
        "nearest_medoid_event_id": int(medoid_indices[nearest_medoid_position] + 1),
        "nearest_medoid_distance": nearest_distance,
        "threshold": threshold,
        "distances_to_medoids": distances_to_medoids,
        "all_matrix": distances_to_all_templates,
        "min_dist": float(np.min(distances_to_all_templates)),
        "mean_dist": float(np.mean(distances_to_all_templates)),
        "median_dist": float(np.median(distances_to_all_templates)),
        "max_dist": float(np.max(distances_to_all_templates)),
        "std_dist": float(np.std(distances_to_all_templates, ddof=1)),
    }

    return assigned_cluster, output
