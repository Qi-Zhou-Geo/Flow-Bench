#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou and Sibashish Dash, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import yaml

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

from scipy.stats import linregress
from scipy.stats import t as student_t  # Student's t-distribution
from scipy.stats import gaussian_kde

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path

current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys

sys.path.append(str(project_root))
# </editor-fold>


# import the custom functions
from pipeline.fit_slope.main import set_st_path
from data.noise_model.visualize_noise_model import plot_Wolin2019_model
from functions.toolkit.confidence_level_test import statistical_testing, statistical_quantile_range

plt.rcParams.update({'font.size': 7,
                     'font.family': "Arial",
                     'axes.formatter.limits': (-4, 6),
                     'axes.formatter.use_mathtext': True})

def load_cached_psd(idx):
    # <editor-fold desc="prepare data">
    default_data_path = f"{project_root}/config/data_path.yaml"
    with open(default_data_path, "r") as f:
        config = yaml.safe_load(f)
        sac_path = config[f"glic_sac_dir"]
        event_catalog_version = config[f"event_catalog_version"]

    file_path = f"{project_root}/data/event_catalog/{event_catalog_version}"
    df = pd.read_csv(f"{file_path}", header=0)

    row_idx = df.loc[idx] # select row_idx
    continent = row_idx["Continent"]
    catchment = row_idx["Catchment"]
    longitude = row_idx["Longitude-Station(-denote-West)"]
    latitude = row_idx["Latitude-Station(-denote-South)"]
    client = row_idx["Client"]
    seismic_network = row_idx["Network"]
    station = row_idx["Station"]
    location = row_idx["Location"]
    component = row_idx["Component"]
    sps = row_idx["SPS(Hz)"]
    distance = row_idx["Min-Distance2DF-Channel(km)"]
    type_source = row_idx["Type(debris-flow=DF)"]

    data_start = row_idx["Manually-Start-time(UTC+0)"]
    data_end = row_idx["Manually-End-time(UTC+0)"]

    ref4sta_s = row_idx["Ref-Start-time4STA(UTC+0)"]
    ref4sta_e = row_idx["Ref-End-time4STA(UTC+0)"]

    sta_s = row_idx["Start-time(UTC+0)-by-STA/LTA"]
    sta_e = row_idx["End-time(UTC+0)-by-STA/LTA"]
    # </editor-fold>


    output_name = f"{idx+1:03d}-{continent}-{catchment}-{seismic_network}-{station}-{component}"
    temp = np.load(f"{project_root}/data/seismic_temp/psd-freq/{output_name}.npz", allow_pickle=True)
    freq = temp["freq"]
    psd = temp["psd"]
    psd_unit = temp["psd_unit"]

    return freq, psd, psd_unit

def select_event(request_catchment):

    # load all events
    default_data_path = f"{project_root}/config/data_path.yaml"
    with open(default_data_path, "r") as f:
        config = yaml.safe_load(f)
        sac_path = config[f"glic_sac_dir"]
        event_catalog_version = config[f"event_catalog_version"]

    file_path = f"{project_root}/data/event_catalog/{event_catalog_version}"
    df = pd.read_csv(f"{file_path}", header=0)

    request_event_id = []
    request_event_unique_list = []

    for idx, label in enumerate(range(len(df))):

        row_idx = df.loc[idx]
        continent = row_idx["Continent"]
        catchment = row_idx["Catchment"]
        longitude = row_idx["Longitude-Station(-denote-West)"]
        latitude = row_idx["Latitude-Station(-denote-South)"]
        client = row_idx["Client"]
        seismic_network = row_idx["Network"]
        station = row_idx["Station"]
        location = row_idx["Location"]
        component = row_idx["Component"]
        sps = row_idx["SPS(Hz)"]
        distance = row_idx["Min-Distance2DF-Channel(km)"]
        type_source = row_idx["Type(debris-flow=DF)"]

        data_start = row_idx["Manually-Start-time(UTC+0)"]
        data_end = row_idx["Manually-End-time(UTC+0)"]

        ref4sta_s = row_idx["Ref-Start-time4STA(UTC+0)"]
        ref4sta_e = row_idx["Ref-End-time4STA(UTC+0)"]

        sta_s = row_idx["Start-time(UTC+0)-by-STA/LTA"]
        sta_e = row_idx["End-time(UTC+0)-by-STA/LTA"]


        unique_id = None
        if station in ["IGB02", "ILL02", "ILL12"]:
            source = type_source.split("_")[1]
            if source == "WSL":
                unique_id = f"WSL-recorded-{distance}"
            elif source == "GFZ":
                unique_id = f"GFZ-labeled-{distance}"
            else:
                print("error")
        else:
            unique_id = f"{catchment}-{station}-{distance}"

        if catchment == request_catchment:
            request_event_id.append(idx)
            request_event_unique_list.append(unique_id)


    return request_event_unique_list, request_event_id

def plot_contour(ax, slope1, slope2, plot_legend=False):

    x = np.array(slope1)
    y = np.array(slope2)

    xy = np.vstack([x, y])
    kde = gaussian_kde(xy)
    padding = 0.2 * (x.max() - x.min())
    xmin, xmax = x.min() - padding, x.max() + padding
    ymin, ymax = y.min() - padding, y.max() + padding

    # Evaluate on a grid
    X, Y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
    positions = np.vstack([X.ravel(), Y.ravel()])
    Z = np.reshape(kde(positions).T, X.shape)

    Z_flat = Z.flatten()
    Z_sorted = np.sort(Z_flat)[::-1]  # high to low
    cumulative = np.cumsum(Z_sorted)
    cumulative /= cumulative[-1]  # normalize to 1

    levels = []
    # Encloses the top 25% of the probability mass
    pro_threshold = [0.1, 0.5, 0.9]
    for threshold in pro_threshold:
        idx = np.searchsorted(cumulative, threshold)
        levels.append(Z_sorted[idx])

    levels = sorted(levels)

    # plot
    contour = ax.contour(X, Y, Z, levels=levels, colors='black', linewidths=0.5, zorder=1)

    # Force the figure to render (needed in Jupyter/inline backends)
    ax.figure.canvas.draw()
    # Use allsegs to get the contour paths safely
    if contour.allsegs and len(contour.allsegs[0]) > 0:
        # allsegs[0] is the first level, [0] is the first path
        p= contour.allsegs[0][0]  # Nx2 array
        x_vals = p[:, 0]
        y_vals = p[:, 1]
    else:
        raise ValueError("No contour paths found. Check your data or levels.")



    x_min = x_vals.min()
    x_max = x_vals.max()

    y_min = y_vals.min()
    y_max = y_vals.max()

    if plot_legend is True:
        print("x_min, x_max, y_min, y_max", x_min, x_max, y_min, y_max)

    # plot area
    x_start = np.round(x_min, 2)
    x_end = np.round(x_max, 2)
    y_start = np.round(y_min, 2)
    y_end = np.round(y_max, 2)

    x = np.arange(x_start, x_end + 0.1, 0.1)
    ax.fill_between(x, y_start, y_end, color='black', alpha=0.1, zorder=1)

    label_temp = [f"{i * 100}%" for i in pro_threshold]
    if plot_legend is True:
        # add legend
        contour_proxy = mlines.Line2D([], [], color='black', linewidth=0.5,
                                      label=f"Pro. contour lines\n[{', '.join(label_temp)}]")
        fill_proxy = mpatches.Patch(color='black', alpha=0.3,
                                    label=f"Filled region\n[{x_start} to {x_end}, {y_start} to {y_end}]")

        ax.legend(handles=[contour_proxy, fill_proxy], loc="lower left", fontsize=6)

    return ax, x_start, x_end, y_start, y_end, label_temp


def check_event_fall_in_contour(event_idx, ax, slope1, slope2, x_point, y_point):
    x = np.array(slope1)
    y = np.array(slope2)

    xy = np.vstack([x, y])
    kde = gaussian_kde(xy)
    padding = 0.2 * (x.max() - x.min())
    xmin, xmax = x.min() - padding, x.max() + padding
    ymin, ymax = y.min() - padding, y.max() + padding

    # Evaluate on a grid
    X, Y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
    positions = np.vstack([X.ravel(), Y.ravel()])
    Z = np.reshape(kde(positions).T, X.shape)

    Z_flat = Z.flatten()
    Z_sorted = np.sort(Z_flat)[::-1]  # high to low
    cumulative = np.cumsum(Z_sorted)
    cumulative /= cumulative[-1]  # normalize to 1

    # Compute KDE contour levels
    pro_threshold = [0.1, 0.5, 0.9]  # top 10%, 50%, 90%
    levels = []
    for threshold in pro_threshold:
        idx = np.searchsorted(cumulative, threshold)
        levels.append(Z_sorted[idx])
    levels = sorted(levels)

    # Plot contours
    contour = ax.contour(X, Y, Z, levels=levels, colors='black', linewidths=0.5, zorder=1)

    # Check each contour level
    results = []
    for i, collection in enumerate(contour.collections):
        # We take the first path in the collection
        path = collection.get_paths()[0]
        inside = "yes, 1" if path.contains_point([x_point, y_point]) else "no, 0"
        results.append(f"{int(pro_threshold[i]*100)}%, {inside}")

    # Fill the bounding area for visualization
    # Using the top contour (10%) to define the bounding rectangle
    p_top = contour.collections[0].get_paths()[0]
    v_top = p_top.vertices
    x_vals, y_vals = v_top[:, 0], v_top[:, 1]
    x_start, x_end = x_vals.min(), x_vals.max()
    y_start, y_end = y_vals.min(), y_vals.max()
    x_fill = np.arange(x_start, x_end + 0.1, 0.1)
    ax.fill_between(x_fill, y_start, y_end, color='black', alpha=0.1, zorder=1)

    # Check if point is inside the filled bounding area
    inside_area = "yes, 1" if (x_start <= x_point <= x_end and y_start <= y_point <= y_end) else "no, 0"
    results.append(f"area, {inside_area}")
    results.append(f"event_idx (the first is event 1), {event_idx+1}")
    # Print results in requested format
    results = ", ".join(results)
    print(results)

    return results

def plot_single_psd(idx, ax, color, marker, label):

    freq, psd, psd_unit = load_cached_psd(idx)

    ax.plot(freq, psd, alpha=0.75, lw=1.5, zorder=3, color=color, label=label)
    ax.set_xscale("log")
    ax.set_xlim(1, 50)
    ax.set_ylim(-200, -50)

def plot_single_slope(idx, ax, color_marker_label_map, clip_min=0, clip_max=10, zorder=5):

    # <editor-fold desc="prepare data">
    default_data_path = f"{project_root}/config/data_path.yaml"
    with open(default_data_path, "r") as f:
        config = yaml.safe_load(f)
        sac_path = config[f"glic_sac_dir"]
        event_catalog_version = config[f"event_catalog_version"]

    file_path = f"{project_root}/data/event_catalog/{event_catalog_version}"
    df = pd.read_csv(f"{file_path}", header=0)

    row_idx = df.loc[idx] # select row_idx
    continent = row_idx["Continent"]
    catchment = row_idx["Catchment"]
    longitude = row_idx["Longitude-Station(-denote-West)"]
    latitude = row_idx["Latitude-Station(-denote-South)"]
    client = row_idx["Client"]
    seismic_network = row_idx["Network"]
    station = row_idx["Station"]
    location = row_idx["Location"]
    component = row_idx["Component"]
    sps = row_idx["SPS(Hz)"]
    distance = row_idx["Min-Distance2DF-Channel(km)"]
    type_source = row_idx["Type(debris-flow=DF)"]

    data_start = row_idx["Manually-Start-time(UTC+0)"]
    data_end = row_idx["Manually-End-time(UTC+0)"]

    ref4sta_s = row_idx["Ref-Start-time4STA(UTC+0)"]
    ref4sta_e = row_idx["Ref-End-time4STA(UTC+0)"]

    sta_s = row_idx["Start-time(UTC+0)-by-STA/LTA"]
    sta_e = row_idx["End-time(UTC+0)-by-STA/LTA"]
    # </editor-fold>

    df2 = pd.read_csv(f"{project_root}/pipeline/fit_slope/fitted_slope.txt", header=None)
    df2 = np.array(df2)
    slope_left = df2[:, 1].astype(float)
    slope_left = np.clip(slope_left, clip_min, clip_max)
    slope_left_CI1 = df2[:, 2].astype(float)
    slope_left_CI2 = df2[:, 3].astype(float)

    slope_right = df2[:, 9].astype(float)
    slope_right = np.clip(slope_right, -1 * clip_max, clip_min)
    slope_right_CI1 = df2[:, 10].astype(float)
    slope_right_CI2 = df2[:, 11].astype(float)

    xerr = slope_left_CI2[idx] - slope_left_CI1[idx]
    yerr = slope_right_CI2[idx] - slope_right_CI1[idx]

    if np.isnan(slope_left[idx]):
        s1 = clip_max
    else:
        s1 = slope_left[idx]

    if np.isnan(slope_right[idx]):
        s2 = clip_max
    else:
        s2 = slope_right[idx]

    if np.isnan(xerr):
        xerr = clip_max

    if np.isnan(yerr):
        yerr = clip_max


    unique_id = None
    if station in ["IGB02", "ILL02", "ILL12"]:
        source = type_source.split("_")[1]
        if source == "WSL":
            unique_id = f"WSL-recorded-{distance}"
        elif source == "GFZ":
            unique_id = f"GFZ-labeled-{distance}"
        else:
            print("error")
    else:
        unique_id = f"{catchment}-{station}-{distance}"

    color_marker_label = color_marker_label_map.get(unique_id)
    label = unique_id
    color, marker = color_marker_label.split("-")

    ax.errorbar(s1, s2,
                xerr=xerr, yerr=yerr,
                color=color,
                label=label,
                marker=marker,
                alpha=0.5,
                zorder=zorder)

    delta = 0.5
    ax.set_xlim(clip_min - delta, clip_max + delta)
    ax.set_ylim(-1 * clip_max - delta, clip_min + delta)

    return s1, s2, xerr, yerr

def plot_ILL_noise_model(ax, request_catchment="Illgraben", print_log=False):


    color_marker_label = mapping_color_marker_label()
    request_event_unique_list, request_event_id = select_event(request_catchment)


    # dump it
    cache_file = Path(f"{project_root}/data/seismic_temp/npz/events_cache.npz")
    if cache_file.exists():
        # Load cached data
        data = np.load(cache_file, allow_pickle=True)
        WSL_event = data["WSL_event"].tolist()
        GFZ_event = data["GFZ_event"].tolist()
        freq = data["freq"].tolist()
    else:
        WSL_event = []
        GFZ_event = []

        for idx, unique_id in zip(request_event_id, request_event_unique_list):
            freq, psd, psd_unit = load_cached_psd(idx)

            if unique_id[:3] == "WSL":
                WSL_event.append(psd)
            elif unique_id[:3] == "GFZ":
                GFZ_event.append(psd)
            else:
                print("Error! check the <plot_ILL_noise_model>")

        np.savez_compressed(cache_file, WSL_event=WSL_event, GFZ_event=GFZ_event, freq=freq)


    plot_label = ["WSL-recorded\n(52 events)", "GFZ-labeled\n(14 events)"]
    colors = ["C2", "C0"]
    for idx, input_data in enumerate([WSL_event, GFZ_event]):
        input_data = np.array(input_data)

        output_mean, output_ci_range, output_lower_q, output_upper_q = statistical_quantile_range(input_data,
                                                                                                  row_or_column="column",
                                                                                                  lower_q=5,
                                                                                                  upper_q=95)
        if print_log is True:
            print(plot_label[idx], input_data.shape)
            print("peak freq.", freq[np.argmax(output_mean)])
        ci_lowers, ci_uppers = output_lower_q, output_upper_q

        ax.plot(freq, output_mean, color=colors[idx], lw=1, zorder=2)
        ax.fill_between(freq, ci_lowers, ci_uppers,
                        color=colors[idx],
                        label=f"{plot_label[idx]}",
                        alpha=0.5, zorder=1)


def mapping_color_marker_label(selected_event=139):

    # <editor-fold desc="prepare data">
    default_data_path = f"{project_root}/config/data_path.yaml"
    with open(default_data_path, "r") as f:
        config = yaml.safe_load(f)
        sac_path = config[f"glic_sac_dir"]
        event_catalog_version = config[f"event_catalog_version"]

    file_path = f"{project_root}/data/event_catalog/{event_catalog_version}"
    df = pd.read_csv(f"{file_path}", header=0, nrows=selected_event)
    # </editor-fold>

    # Define color cycle
    color_cycle = [f"C{i}" for i in range(9)]
    color_cycle.remove('C0')  # reserve for GFZ labeled
    color_cycle.remove('C2')  # reserve for WSL recorded
    # color_cycle.remove('C5') # brown, not good
    # color_cycle.remove('C6') # pink, not good
    # color_cycle.remove('C7') # gray, not good
    color_cycle.append("gold")
    color_cycle.append("blue")
    color_cycle.append("black")
    # color_cycle.append("lime")
    marker_cycle = ["o", "^", "s", "*"]

    # make the unique combinations
    color_marker = []
    for j in marker_cycle:
        for i in color_cycle:
            color_marker.append(f"{i}-{j}")

    if 'C0-o' in color_marker:
        color_marker.remove('C0-o')
    if 'C2-o' in color_marker:
        color_marker.remove('C2-o')
    # put this at the "top"
    color_marker = ['C0-o', 'C2-o'] + color_marker

    # make the unique catchment-station combinations
    unique_id_list = []
    for idx in range(len(df)):

        row_idx = df.loc[idx]

        station = row_idx["Station"]
        distance = row_idx["Min-Distance2DF-Channel(km)"]
        type_source = row_idx["Type(debris-flow=DF)"]
        catchment = row_idx["Catchment"]

        unique_id = None
        if station in ["IGB02", "ILL02", "ILL12"]:
            source = type_source.split("_")[1]
            if source == "WSL":
                unique_id = f"WSL-recorded-{distance}"
            elif source == "GFZ":
                unique_id = f"GFZ-labeled-{distance}"
            else:
                print("error")
        else:
            unique_id = f"{catchment}-{station}-{distance}"

        unique_id_list.append(unique_id)

    unique_id_list = np.unique(unique_id_list)
    unique_id_list = unique_id_list.tolist()
    # Sort by the numeric source-receiver-distance value after the last '-'
    unique_id_list = sorted(unique_id_list, key=lambda x: float(x.split('-')[-1]))

    # make C0-o to GFZ label, C2-0 to WSL label
    if 'WSL-recorded-0.09' in unique_id_list:
        unique_id_list.remove('WSL-recorded-0.09')
    if 'GFZ-labeled-0.09' in unique_id_list:
        unique_id_list.remove('GFZ-labeled-0.09')
    unique_id_list = ['GFZ-labeled-0.09', 'WSL-recorded-0.09'] + unique_id_list

    if len(unique_id_list) > len(color_marker):
        print(f"Warning! len(unique_id_list) {len(unique_id_list)} > len(color_marker) {len(color_marker)}")

    # mapping the unique id with color-marker
    color_marker_label = {}
    for idx, (i, j) in enumerate(zip(unique_id_list, color_marker)):
        color_marker_label[i] = j

    return color_marker_label


def make_manual_legend_handles(mapping, alpha=0.5, edgecolor="black"):
    handles = []
    # split entry into (color, marker)
    items = [
        (name, val.split("-")[0], val.split("-")[1])
        for name, val in mapping.items()
    ]

    # sort by color → marker → name
    items_sorted = sorted(items, key=lambda x: (x[1], x[2], x[0]))

    for name, color, marker in items_sorted:
        clean_name = name.replace("Mount_", "")
        temp = clean_name.split("_")
        temp = "-".join(temp)

        handle = mlines.Line2D(
            [], [],
            color=color,
            markeredgecolor=edgecolor,
            marker=marker,
            linestyle='None',
            markersize=6,
            alpha=alpha,
            label=f"{temp}"
        )
        handles.append(handle)
    return handles


fig, ax = plt.subplots()
plot_ILL_noise_model(ax)