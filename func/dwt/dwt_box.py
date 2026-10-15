#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-12T15:14:42
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np

import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator


from scipy.ndimage import uniform_filter1d

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

plt.rcParams.update(
    {
        "font.size": 7,
        "font.family": "Arial",
        "axes.formatter.limits": (-4, 6),
        "axes.formatter.use_mathtext": True,
    }
)


def box_plot_dtw_distance_by_cluster(
    distance_matrix,
    cluster_labels,
    save_path,
    start_index=1,
    xlim=(0, 3.5),
    exclude_self=False,
):
    """
    Plot per-event DTW distance distributions, colored by cluster.

    Args:
        distance_matrix: Pairwise DTW distance matrix. Can be square or rectangular.
        cluster_labels: Cluster label for each row/event.
        save_path: Path to save the figure.
        start_index: First event index for y-axis labels.
        xlim: x-axis limits.
        exclude_self: Set True only when rows and columns are the same events in the same order.
    """
    distance_matrix = np.asarray(distance_matrix, dtype=float)
    cluster_labels = np.asarray(cluster_labels)

    if distance_matrix.ndim != 2 or 0 in distance_matrix.shape:
        raise ValueError("distance_matrix must be a nonempty two-dimensional array.")
    if not np.all(np.isfinite(distance_matrix)) or np.any(distance_matrix < 0):
        raise ValueError("DTW distances must be finite and nonnegative.")
    if cluster_labels.ndim != 1:
        raise ValueError("cluster_labels must be one-dimensional.")

    num_events = distance_matrix.shape[0]
    if exclude_self and (distance_matrix.shape[1] != num_events or num_events < 2):
        raise ValueError("exclude_self=True requires a square matrix with at least two events.")

    if len(cluster_labels) != num_events:
        raise ValueError(
            f"cluster_labels length ({len(cluster_labels)}) must match number of rows in distance_matrix ({num_events})"
        )

    event_labels = [f"{start_index + i:03d}" for i in range(num_events)]

    base_colors = ["C0", "C2", "#630C3A", "#D3500C", "#39C8C6"]
    unique_clusters = sorted(np.unique(cluster_labels))

    colors = {}
    for cluster in unique_clusters:
        if cluster not in [1, 2, 3, 4, 5]:
            raise ValueError("Cluster labels must be integers from 1 to 5.")
        colors[cluster] = base_colors[int(cluster) - 1]

    box_data = []

    for i in range(num_events):
        if exclude_self:
            distances = np.delete(distance_matrix[i, :], i)
        else:
            distances = distance_matrix[i, :]

        box_data.append(distances)

    fig = plt.figure(figsize=(5, 6))
    gs = gridspec.GridSpec(1, 1)
    ax = plt.subplot(gs[0])

    boxplot = ax.boxplot(
        box_data,
        orientation="horizontal",
        tick_labels=event_labels,
        patch_artist=True,
        showfliers=True,
        flierprops={
            "marker": "o",
            "markersize": 2,
            "alpha": 0.5,
        },
        medianprops={"color": "black", "lw": 1},
        whiskerprops={"color": "black", "lw": 0.5},
        capprops={"color": "black", "lw": 0.5},
    )

    for i, box in enumerate(boxplot["boxes"]):
        cluster = cluster_labels[i]
        color = colors[cluster]

        box.set_facecolor(color)
        box.set_edgecolor("black")
        box.set_alpha(0.5)
        box.set_linewidth(0.5)

        flier = boxplot["fliers"][i]
        flier.set_markeredgecolor(color)
        flier.set_markerfacecolor("none")
        flier.set_alpha(0.5)
        flier.set_markersize(2)

    legend_handles = []
    for cluster in unique_clusters:
        legend_handles.append(
            Patch(
                facecolor=colors[cluster],
                edgecolor="black",
                alpha=0.45,
                label="Unassigned (4)" if cluster == 4 else f"Cluster {cluster}",
            )
        )

    first_event = start_index
    last_event = start_index + num_events - 1

    major_event_ids = [first_event]
    first_round_10 = ((first_event // 10) + 1) * 10

    for event_id in range(first_round_10, last_event + 1, 10):
        major_event_ids.append(event_id)

    major_event_ids.append(last_event)
    major_event_ids = sorted(set(major_event_ids))

    major_tick_positions = []
    major_tick_labels = []

    for event_id in major_event_ids:
        pos = event_id - start_index + 1
        major_tick_positions.append(pos)
        major_tick_labels.append(f"{event_id:03d}")

    ax.set_yticks(major_tick_positions)
    ax.set_yticklabels(major_tick_labels)
    ax.yaxis.set_minor_locator(MultipleLocator(1))

    if xlim is not None:
        ax.set_xlim(*xlim)

    ax.invert_yaxis()
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.tick_params(axis="y", which="both", left=False, right=True, labelleft=False, labelright=True)
    ax.set_ylim(0.5, num_events + 0.5)
    ax.yaxis.tick_left()
    ax.yaxis.set_label_position("left")
    ax.tick_params(axis="y", which="both", left=True, right=False, labelleft=True, labelright=False)

    ax.legend(
        handles=legend_handles,
        loc="lower right",
        fontsize=6,
        labelspacing=0.25,
        handlelength=1.2,
    )

    ax.set_xlabel("Dynamic Time Warping Distance", fontweight="bold")
    ax.set_ylabel("Event Index", fontweight="bold")
    ax.grid(axis="x", ls="--", color="grey", lw=0.5, alpha=0.5)

    plt.tight_layout()
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=600, bbox_inches=None)
    plt.show()
    plt.close(fig=fig)


def plot_clustered_traces(
    traces_amp,
    traces_meta,
    traces_cluster_labels,
    name,
    max_clusters=5,
    medoid_indices=None,
    template_details=None,
):

    colors = ["C0", "C2", "#630C3A", "#D3500C", "#39C8C6"]
    traces_cluster_labels = np.asarray(traces_cluster_labels)
    if traces_cluster_labels.ndim != 1 or not (len(traces_amp) == len(traces_meta) == len(traces_cluster_labels)):
        raise ValueError("Traces, metadata, and one-dimensional labels must have matching lengths.")
    if len(traces_amp) == 0:
        raise ValueError("No traces to plot.")
    if not set(traces_cluster_labels).issubset([1, 2, 3, 4, 5]):
        raise ValueError("Cluster labels must be integers from 1 to 5.")
    unique_clusters = sorted(np.unique(traces_cluster_labels))

    if len(unique_clusters) > max_clusters:
        raise ValueError(f"Expected at most {max_clusters} clusters, got {len(unique_clusters)}")

    height = min(2.0 * len(unique_clusters), 7.5)

    if template_details is None:
        template_details = {
            41: "Single dominant surge",
            19: "Multiple post-peak surges",
            15: "Multiple pre-peak surges",
        }

    if medoid_indices is None:
        medoid_indices = []
    else:
        medoid_indices = list(medoid_indices)

    for medoid_idx in medoid_indices:
        if not isinstance(medoid_idx, (int, np.integer)) or not 0 <= medoid_idx < len(traces_amp):
            raise ValueError("Medoid indices must be valid zero-based trace indices.")

    fig = plt.figure(figsize=(6, height))
    gs = gridspec.GridSpec(len(unique_clusters), 1)

    axes = {}
    cluster_text = {}

    for idx, cluster in enumerate(unique_clusters):
        axes[cluster] = plt.subplot(gs[idx])
        cluster_text[cluster] = []

    for trace_idx, (amp, meta, cluster) in enumerate(zip(traces_amp, traces_meta, traces_cluster_labels)):
        ##
        amp = np.asarray(amp, dtype=float)
        if amp.ndim != 1 or len(amp) == 0 or not np.all(np.isfinite(amp)):
            raise ValueError(f"Trace {trace_idx} must be a finite, nonempty one-dimensional array.")
        amp_energy = uniform_filter1d(amp**2, size=19)
        max_amp = np.argmax(amp_energy)
        index = (np.arange(len(amp)) - max_amp) * 10 / 3600  # convert to hours

        if cluster not in axes:
            raise ValueError(f"Please check the cluster: {cluster}")

        ax = axes[cluster]
        color = colors[int(cluster) - 1]

        event_id = f"{int(meta[:3]) + 1:03d}"
        cluster_text[cluster].append(event_id)

        if trace_idx in medoid_indices:
            template_label = f"Template Event ID: {event_id}"
            if trace_idx in template_details:
                template_label += f"\n{template_details[trace_idx]}"

            ax.plot(
                index,
                amp,
                color="black",
                lw=1.2,
                alpha=0.8,
                ls="-",
                zorder=5,
                label=template_label,
            )
        else:
            ax.plot(index, amp, color=color, alpha=0.5, lw=1, zorder=2)

    for idx, cluster in enumerate(unique_clusters):
        ax = axes[cluster]

        title = "Unassigned (4)" if cluster == 4 else f"Cluster {cluster}"
        ax.set_title(label=f"({chr(97 + idx)}) {title}", fontsize=7, loc="left", fontweight="bold")

        ax.set_xlim(-1.5, 1.5)
        ax.set_xticks([-1.5, -1.0, 0, 1, 1.5], [-1.5, -1.0, 0, 1, 1.5])
        ax.set_ylim(0, 1)
        ax.set_xlabel("")
        ax.set_ylabel("")

        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.xaxis.set_minor_locator(MultipleLocator(1 / 6))
        ax.grid(ls="--", color="grey", lw=0.5, alpha=0.5, zorder=1)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc="upper right", fontsize=6)

        ids = cluster_text[cluster]
        rows = ["Event ID:"]
        for i in range(0, len(ids), 5):
            row = ", ".join(ids[i : i + 5])
            rows.append(row)

        text = "\n".join(rows)
        ax.text(0.02, 0.95, text, transform=ax.transAxes, ha="left", va="top", fontsize=6, color="black")

    fig.supxlabel("Time Relative to Peak Amplitude [hours]", fontsize=7, fontweight="bold")
    fig.supylabel("Normalized Root-Mean-Square Amplitude", fontsize=7, fontweight="bold")

    plt.tight_layout()
    save_path = Path(project_root) / "plots/fig3" / f"{name}.png"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=600, bbox_inches=None)
    plt.show()
    plt.close(fig=fig)
