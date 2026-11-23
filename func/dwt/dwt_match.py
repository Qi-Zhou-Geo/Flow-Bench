#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-02T15:28:12
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
from dtaidistance import dtw


def assign_dtw_cluster(obs_trace, template_traces):

    # all available traces
    template_traces_arr = np.array(template_traces, dtype=object)

    # Step 1
    # build the DTW pari matrix
    distance_matrix = []
    for trace in template_traces_arr:
        # (1)
        # one template trace from the template
        trace = np.array(trace, dtype=float)

        # (2)
        # current obsved trace
        obs_trace = np.array(obs_trace, dtype=float)

        # (3)
        # calcualte the DTW for the current pair
        distance = dtw.distance_fast(obs_trace, trace)

        # (4)
        # add to container
        distance_matrix.append(distance)

    # Step 2
    # stastic
    min_dist = np.min(distance_matrix)
    mean_dist = np.mean(distance_matrix)
    median_dist = np.median(distance_matrix)
    max_dist = np.max(distance_matrix)
    std_dist = np.std(distance_matrix, ddof=1)  # sample standard deviation

    q05 = np.percentile(distance_matrix, 5)
    q50 = np.percentile(distance_matrix, 50)
    q95 = np.percentile(distance_matrix, 95)

    output = {
        # mean
        "min_dist": f"{min_dist:.4f}",
        "mean_dist": f"{mean_dist:.4f}",
        "median_dist": f"{median_dist:.4f}",
        "max_dist": f"{max_dist:.4f}",
        "std_dist": f"{std_dist:.4f}",
        # quatile
        "q05": f"{q05:.4f}",
        "q50": f"{q50:.4f}",
        "q95": f"{q95:.4f}",
        # all
        "all_matrix": distance_matrix,
        "num_ref_traces": len(template_traces_arr),
    }

    return output, distance_matrix
