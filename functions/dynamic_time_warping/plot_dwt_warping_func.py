#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou and Sibashish Dash, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import array
from collections import defaultdict
import textwrap

import numpy as np
import pandas as pd

from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from sklearn.metrics import silhouette_score

from dtaidistance import dtw
from dtaidistance import dtw_visualisation as dtwvis

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MultipleLocator

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path

current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy

project_root = current_dir.parent.parent
import sys

sys.path.append(str(project_root))
# </editor-fold>

# import the custom functions
from functions.dynamic_time_warping.dwt_warping import min_max_normalize
from functions.color_of_noise.plot_psd_slope_func import make_manual_legend_handles

plt.rcParams.update({'font.size': 7,
                     'font.family': "Arial",
                     'axes.formatter.limits': (-4, 6),
                     'axes.formatter.use_mathtext': True})


def plot_elbow(linked):
    merge_distances = linked[:, 2]  # distance of each merge
    x = range(1, len(merge_distances) + 1)

    fig = plt.figure(figsize=(4, 4))
    gs = gridspec.GridSpec(1, 1)
    ax = plt.subplot(gs[0, 0])

    plt.scatter(x, merge_distances[::-1], color="black", alpha=0.5, zorder=2)
    plt.plot(x, merge_distances[::-1], color="black", alpha=0.5, zorder=1)

    plt.plot(x, x, color="C0", ls="-", lw=1, alpha=0.8, label="1:1 line", zorder=1)

    plt.xlabel("Merge DTW Distance in Reverse Order", fontweight='bold')
    plt.ylabel("DTW Distance", fontweight='bold')
    plt.ylim(0, np.max(merge_distances[::-1]) + 1)
    plt.legend(loc="upper right", fontsize=6)
    ax.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.5, zorder=1)

    plt.tight_layout()
    plt.savefig(f"{project_root}/plotting/dwt_cluster/Elbow-Detection.png", dpi=600)
    plt.show()
    plt.close(fig=fig)


def plot_silhouette_score(linked, distance_matrix):
    scores = {}
    for k in range(2, 60):
        labels = fcluster(linked, k, criterion='maxclust')

        score = silhouette_score(distance_matrix, labels, metric="precomputed")
        scores[k] = score

    x = list(scores.keys())
    y = list(scores.values())

    fig = plt.figure(figsize=(4, 4))
    gs = gridspec.GridSpec(1, 1)
    ax = plt.subplot(gs[0, 0])

    ax.text(x=10, y=0.5, s=f"Max Silhouette Score = {max(y):.2f}\n"
                           f"when Number of clusters = {x[np.argmax(y)]}")

    ax.scatter(x, y, color="black", alpha=0.5, zorder=2)
    ax.plot(x, y, color="black", zorder=1)
    ax.set_ylim(0, 0.6)
    ax.set_xlabel("Number of clusters", fontweight='bold')
    ax.set_ylabel("Silhouette Score for DTW", fontweight='bold')

    ax.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.5, zorder=1)

    plt.tight_layout()
    plt.savefig(f"{project_root}/plotting/dwt_cluster/silhouette_score.png", dpi=600)
    plt.show()
    plt.close(fig=fig)


def plot_elbow_silhouette(linked, distance_matrix):
    scores = {}
    for k in range(2, 60):
        labels = fcluster(linked, k, criterion='maxclust')

        score = silhouette_score(distance_matrix, labels, metric="precomputed")
        scores[k] = score

    x = list(scores.keys())
    y = list(scores.values())

    fig = plt.figure(figsize=(5.5, 3.5))
    gs = gridspec.GridSpec(1, 2)
    ax = plt.subplot(gs[1])
    ax.set_title("(b)", fontweight='bold', fontsize=7, loc='left')
    label = (f"Max Silhouette Score = {max(y):.2f} "
             f"when Number of clusters = {x[np.argmax(y)]}")
    print(label)
    # ax.text(x=10, y=0.5, s=f"Max Silhouette Score = {max(y):.2f}\n"
    #                        f"when Number of clusters = {x[np.argmax(y)]}")

    ax.scatter(x, y, color="black", alpha=0.5, zorder=2)
    ax.plot(x, y, color="black", zorder=1)
    ax.axvline(x=3, ls="--", lw=1, color="gray")
    ax.set_ylim(0, 0.6)
    ax.set_xlim(1, 60)
    ax.set_xticks([1, 10, 20, 30, 40, 50, 60], [1, 10, 20, 30, 40, 50, 60])
    ax.set_xlabel("Number of Clusters", fontweight='bold')
    ax.set_ylabel("Silhouette Score", fontweight='bold')

    ax.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.5, zorder=1)

    # emblow
    ax = plt.subplot(gs[0])
    ax.set_title("(a)", fontweight='bold', fontsize=7, loc='left')
    merge_distances = linked[:, 2]  # distance of each merge
    x = range(1, len(merge_distances) + 1)

    plt.scatter(x, merge_distances[::-1], color="black", alpha=0.5, zorder=2)
    plt.plot(x, merge_distances[::-1], color="black", alpha=0.5, zorder=1)
    ax.axvline(x=3, ls="--", lw=1, color="gray")
    ax.set_xlim(1, 60)
    ax.set_xticks([1, 10, 20, 30, 40, 50, 60], [1, 10, 20, 30, 40, 50, 60])
    plt.xlabel("Number of Clusters", fontweight="bold")
    plt.ylabel("DTW Distance", fontweight='bold')
    plt.ylim(0, np.max(merge_distances[::-1]) + 1)
    ax.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.5, zorder=1)

    plt.tight_layout()
    plt.savefig(f"{project_root}/pipeline/cal_dwt_matrix/elbow_silhouette.png", dpi=600)
    plt.show()
    plt.close(fig=fig)


def leaf_label_func(id, t=1, event_source="ILL"):
    file_path = (current_dir / f"../../../config/manually_labeled_DF/all_collected_events.txt").resolve()
    df = pd.read_csv(f"{file_path}", header=0)
    data_arr = np.array(df)
    seismic_network = data_arr[id, 6]
    event_type = data_arr[id, 14][-3:]

    if event_source == "ILL":
        # label = f"{id+1} ({seismic_network}-{event_type})"

        if f"{seismic_network}-{event_type}" == "9J-GFZ":
            label = f"{id + t}*"
        else:
            label = f"{id + t}"
    else:
        label = f"{float(id) + float(t)}"

    return label


def plot_traces_by_label(obj_trace, color_marker_label_map):
    temp = np.load(f"{project_root}/pipeline/cal_dwt_matrix/traces_amp_{obj_trace}.npz", allow_pickle=True)

    denoise_time_window_size = temp['denoise_time_window_size']
    unique_id_list = temp["unique_id_list"]
    traces_amp_index = temp["traces_amp_index"]
    traces_amp = temp["traces_amp"]
    traces_cluster_labels = temp["traces_cluster_labels"]

    unique_labels = np.unique(traces_cluster_labels)

    fig = plt.figure(figsize=(6, 4))
    gs = gridspec.GridSpec(len(unique_labels), 1)

    axes = {}
    for cluster in unique_labels:
        axes[cluster] = plt.subplot(gs[cluster - 1])

    temp = zip(traces_amp_index, traces_amp, traces_cluster_labels, unique_id_list)
    for index, amp, cluster, unique_id in temp:
        ax = axes.get(cluster)
        index = index.astype(float) * denoise_time_window_size / 60  # convert to minute
        amp = amp.astype(float)

        color_marker_label = color_marker_label_map.get(unique_id)
        label = unique_id
        color, marker = color_marker_label.split("-")

        # ax.plot(index, amp, color=color, marker=marker, alpha=0.3, markevery=60)
        # ax.plot(index, amp, color=color, alpha=0.3, zorder=2)
        dt = 10
        energy = np.cumsum(amp ** 2) * dt
        energy = min_max_normalize(energy)
        # ax.plot(index, energy, color=color, alpha=0.6, zorder=2)
        ax.plot(index, energy, color=color, marker=marker, markeredgecolor="#7F7F7F",
                alpha=0.6, markevery=180, markersize=6)
        # ax.set_yscale('log')

        ax.set_xlim(-240, 240)
        # ax.set_ylim(1e-4, 1e0)
        ax.set_xlabel("")  # remove axis label
        ax.xaxis.set_major_locator(MultipleLocator(60))
        ax.xaxis.set_minor_locator(MultipleLocator(10))
        ax.grid(ls="--", color="grey", lw=0.5, alpha=0.5, zorder=1)

    for cluster in unique_labels:
        ax = axes.get(cluster)
        ax.text(x=ax.get_xlim()[0], y=0.8, s=f" Cluster {cluster}",
                fontweight='bold', ha="left", va="top")

        event_index = np.where(traces_cluster_labels == cluster)[0] + 1
        label = []
        for e in event_index:
            label.append(f"{e:02d}")

        # add WSl and GFZ
        # label = []
        # for i in event_index:
        #     j = unique_id_list[i-1]
        #     j = str(j).split("-")[0]
        #     if j == "GFZ":
        #         label.append(f"{i}({j})")
        #     else:
        #         label.append(f"{i}")

        event_index = np.array(label)
        event_index = event_index.astype(str)
        chunk_size = 10
        lines = []
        for i in range(0, len(event_index), chunk_size):
            l = ", ".join(event_index[i:i + chunk_size])
            lines.append(f" {l}")

        event_text = "\n".join(lines)
        # add text in plot
        ax.text(x=ax.get_xlim()[0], y=0.6, s=f" Event Index:\n{event_text}",
                ha="left", va="top")
        print(f" Cluster {cluster}\n"
              f"{event_text}")

        ax.set_ylabel("Normalized Amplitude", fontweight='bold')
        ax.set_xlabel("Time [minute]", fontweight='bold')

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3)
    plt.savefig(f"{project_root}/plotting/dwt_cluster/Cluster-{obj_trace}.png", dpi=600)  # , transparent=True
    plt.show()
    plt.close(fig=fig)


def leaf_label_func(id, t, event_source="Non-ILL"):
    file_path = (current_dir / f"../../../config/manually_labeled_DF/all_collected_events.txt").resolve()
    df = pd.read_csv(f"{file_path}", header=0)
    data_arr = np.array(df)
    seismic_network = data_arr[id, 6]
    event_type = data_arr[id, 14][-3:]

    if event_source == "ILL":
        # label = f"{id+1} ({seismic_network}-{event_type})"

        if f"{seismic_network}-{event_type}" == "9J-GFZ":
            label = f"{id + t}*"
        else:
            label = f"{id + t}"
    else:
        label = f"{float(id) + float(t)}"

    return label


def plot_tree(linked):
    import matplotlib.patches as mpatches

    fig = plt.figure(figsize=(7, 4))
    gs = gridspec.GridSpec(1, 1)
    ax = plt.subplot(gs[0])

    num_traces = len(linked) + 1
    with plt.rc_context({'lines.linewidth': 0.8}):
        dend = dendrogram(linked,
                          orientation="top",
                          distance_sort='average',
                          show_leaf_counts=True,
                          count_sort=False,
                          leaf_font_size=6,
                          color_threshold=None,
                          above_threshold_color="black",
                          link_color_func=lambda k: 'black',
                          labels=list(range(1, num_traces + 1)))

    for tick in ax.get_xticklabels():
        tick.set_rotation(0)

    ax.grid(ls="--", color="grey", lw=0.5, alpha=0.5, zorder=1)

    ax.set_xlabel("Event Index", fontweight='bold')
    ax.set_ylabel("Dynamic Time Warping Distance", fontweight='bold')

    ax = plt.gca()
    # Get x-axis limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Get leaf positions
    leaf_positions = dend['icoord']
    n_leaves = len(dend['leaves'])

    # cluster_boundaries = [0, num_cluster1, num_cluster1 + num_cluster2, n_leaves]
    cluster_boundaries = [0, 54, 54 + 5, n_leaves]

    # Define colors for each cluster
    colors = ['#ffcccc', '#ccffcc', '#ccccff']

    # Add background rectangles for each cluster
    for i in range(3):
        x_start = cluster_boundaries[i] * 10  # dendrogram x-spacing is 10 by default
        x_end = cluster_boundaries[i + 1] * 10

        rect = mpatches.Rectangle((x_start, ylim[0]),
                                  x_end - x_start,
                                  ylim[1] - ylim[0],
                                  facecolor=colors[i],
                                  alpha=0.3,
                                  zorder=0)  # Put behind everything
        ax.add_patch(rect)

    plt.tight_layout()
    plt.savefig(f"{project_root}/plotting/dwt_cluster/hierarchical-clustering-tree.png", dpi=600)  # , transparent=True
    plt.show()
    plt.close(fig=fig)


def plot_traces_all(event_seperator, color_marker_label_map):
    subplot_index = {"Illgraben Cluster 1": "(a)", "Illgraben Cluster 2": "(b)", "Illgraben Cluster 3": "(c)",
                     "Non-Illgraben Cluster 1": "(d)", "Non-Illgraben Cluster 2": "(e)",
                     "Non-Illgraben Cluster 3": "(f)"}

    fig = plt.figure(figsize=(7, 8))
    gs = gridspec.GridSpec(8, 1, height_ratios=[1, 1, 1, 1, 1, 1, 0.05, 0.5])

    for obj_trace in ["ILL_traces", "non_ILL_traces"]:

        temp = np.load(f"{project_root}/pipeline/cal_dwt_matrix/traces_amp_{obj_trace}.npz", allow_pickle=True)

        denoise_time_window_size = temp['denoise_time_window_size']
        unique_id_list = temp["unique_id_list"]
        traces_amp_index = temp["traces_amp_index"]
        traces_amp = temp["traces_amp"]
        traces_cluster_labels = temp["traces_cluster_labels"]

        unique_labels = np.unique(traces_cluster_labels)
        axes = {}
        if obj_trace == "ILL_traces":
            for cluster in unique_labels:
                axes[cluster] = plt.subplot(gs[cluster - 1])
        else:
            for cluster in unique_labels:
                axes[cluster] = plt.subplot(gs[cluster + 3 - 1])

        temp = zip(traces_amp_index, traces_amp, traces_cluster_labels, unique_id_list)
        for index, amp, cluster, unique_id in temp:
            ax = axes.get(cluster)
            index = index.astype(float) * denoise_time_window_size / 60  # convert to minute
            amp = amp.astype(float)

            color_marker_label = color_marker_label_map.get(unique_id)
            label = unique_id
            color, marker = color_marker_label.split("-")

            # ax.plot(index, amp, color=color, marker=marker, alpha=0.3, markevery=60)
            # ax.plot(index, amp, color=color, alpha=0.3, zorder=2)
            dt = 10
            energy = np.cumsum(amp ** 2) * dt
            energy = min_max_normalize(energy)
            # ax.plot(index, energy, color=color, alpha=0.6, zorder=2)
            ax.plot(index, energy, color=color, marker=marker, markeredgecolor="#7F7F7F",
                    alpha=0.6, markevery=180, markersize=6, label=label)
            # ax.set_yscale('log')

            ax.set_xlim(-180, 180)
            # ax.set_ylim(1e-4, 1e0)
            ax.set_xlabel("")  # remove axis label
            ax.xaxis.set_major_locator(MultipleLocator(60))
            ax.xaxis.set_minor_locator(MultipleLocator(10))
            ax.grid(ls="--", color="grey", lw=0.5, alpha=0.5, zorder=1)

        if obj_trace == "ILL_traces":
            source = "Illgraben"

        else:
            source = "Non-Illgraben"

        for cluster in unique_labels:
            ax = axes.get(cluster)
            subplot_label = f"{source} Cluster {cluster}"
            subplot_label_temp = subplot_index.get(f"{subplot_label}")
            subplot_label = f"{source} Cluster {cluster}"
            ax.text(x=ax.get_xlim()[0], y=0.95, s=f" {subplot_label_temp}\n {subplot_label}",
                    fontweight='bold', ha="left", va="top")

            event_index = np.where(traces_cluster_labels == cluster)[0] + 1

            if obj_trace == "ILL_traces":
                event_index = event_index
            else:
                event_index = event_index + event_seperator

            label = []
            for e in event_index:
                label.append(f"{e:03d}")

            event_index = np.array(label)
            event_index = event_index.astype(str)
            chunk_size = 10
            lines = []
            for i in range(0, len(event_index), chunk_size):
                l = ", ".join(event_index[i:i + chunk_size])
                lines.append(f" {l}")

            event_text = "\n".join(lines)
            # add text in plot
            # ax.text(x=ax.get_xlim()[0], y=0.75, s=f" Event Index:\n{event_text}", ha="left", va="top")
            print(f" Cluster {cluster}\n"
                  f"{event_text}")
            ax.set_xlabel("", fontweight='bold')
            ax.set_ylabel("", fontweight='bold')

    ax = plt.subplot(gs[0])
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(),
              loc="lower right", fontsize=6, ncol=2, columnspacing=0.5)

    ax = plt.subplot(gs[5])
    ax.set_xlabel("Time [minute]", fontweight='bold')
    fig.supylabel("Normalized Cumulative Seismic Energy", fontsize=7, fontweight="bold")

    # add legend
    ax_bar = plt.subplot(gs[7])
    del color_marker_label_map['GFZ-labeled-0.09']
    del color_marker_label_map['WSL-recorded-0.09']
    handles = make_manual_legend_handles(color_marker_label_map)
    legend = ax_bar.legend(
        handles=handles,
        loc="upper center",
        fontsize=6,
        ncol=5,
        frameon=False
    )

    # legend.set_title("Legend\nNon Illgraben catchment-Station-Source receiver distance [km]",
    # prop={"weight": "bold", "size": 6})

    legend.get_title().set_ha("center")
    ax_bar.axis("off")

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.25)
    plt.savefig(f"{project_root}/plotting/dwt_cluster/Cluster-DWT.png", dpi=600)  # , transparent=True
    plt.show()
    plt.close(fig=fig)


def plot_nonILL_statistics(color_marker_label_map, event_seperator=66):

    temp = np.load(f"{project_root}/pipeline/cal_dwt_matrix/traces_dwt_statistics.npz", allow_pickle=True)
    denoise_time_window_size = temp['denoise_time_window_size']
    unique_id_list = temp["unique_id_list"]
    traces_cluster_labels = temp["traces_cluster_labels"]
    nonILL_fitted_all_dwt_d = temp["nonILL_fitted_all_dwt_d"]

    fig = plt.figure(figsize=(6, 8))
    gs = gridspec.GridSpec(1, 3, width_ratios=[10, 3, 1])

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax_bar = fig.add_subplot(gs[2])

    positions = []
    box_data = []
    colors_list = []

    for i in range(len(unique_id_list)):
        unique_id = unique_id_list[i]
        color_marker_label = color_marker_label_map.get(unique_id)
        label = unique_id
        color, marker = color_marker_label.split("-")

        data = nonILL_fitted_all_dwt_d[i]
        positions.append(event_seperator + 1 + i)
        box_data.append(data)
        colors_list.append(color)

        cluster = traces_cluster_labels[i]
        ax2.scatter(cluster,  event_seperator + 1 + i, facecolor=color, edgecolor="black", marker=marker, label=label)

    # Horizontal box plot
    bp = ax1.boxplot(box_data, positions=positions, vert=False, widths=0.6, patch_artist=True)
    # Color each box
    for patch, color in zip(bp['boxes'], colors_list):
        patch.set_facecolor(color)

    ax1.set_title("(a)", fontweight='bold', fontsize=7, loc='left')
    ax1.set_ylim(event_seperator + 0.5, event_seperator + len(unique_id_list) + 0.5)
    ax1.yaxis.set_minor_locator(MultipleLocator(2))
    ax1.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.8, zorder=1)
    ax1.grid(which='minor', axis='y', color='grey', linestyle='--', lw=0.5, alpha=0.8, zorder=1)
    ax1.set_yticks([67, 70, 80, 90, 100, 110, 120, 130, 140],
                   [67, 70, 80, 90, 100, 110, 120, 130, 140])
    ax1.axvline(x=2, color="red", linestyle='--', lw=1, alpha=1, zorder=1)
    ax1.set_xlabel("Dynamic Time Warping (DTW) Distance", fontweight='bold')
    ax1.set_ylabel("Event Index [ID]", fontweight='bold')

    ax2.set_title("(b)", fontweight='bold', fontsize=7, loc='left')
    ax2.set_ylim(event_seperator + 0.5, event_seperator + len(unique_id_list) + 0.5)
    ax2.yaxis.set_minor_locator(MultipleLocator(2))
    ax2.grid(axis='both', color='grey', linestyle='--', lw=0.5, alpha=0.8, zorder=1)
    ax2.grid(which='minor', axis='y', color='grey', linestyle='--', lw=0.5, alpha=0.8, zorder=1)
    ax2.set_yticks([67, 70, 80, 90, 100, 110, 120, 130, 140],
                   [67, 70, 80, 90, 100, 110, 120, 130, 140])
    ax2.set_xlabel("Cluster", fontweight='bold')
    ax2.set_ylabel("", fontweight='bold')

    handles = make_manual_legend_handles(color_marker_label_map, alpha=1)
    legend = ax_bar.legend(
        handles=handles,
        loc="upper left",
        fontsize=6,
        ncol=1,
        frameon=False
    )
    legend.get_title().set_ha("center")
    ax_bar.axis("off")

    plt.tight_layout()
    plt.savefig(f"./non_ILL_DWT_statistics.png", dpi=600, transparent=True)
    plt.show()

