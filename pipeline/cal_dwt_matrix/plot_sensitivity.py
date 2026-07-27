#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-01-20
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import os
import numpy as np
import pandas as pd

from tqdm import tqdm

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
import seaborn as sns


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
from func.dynamic_time_warping.dwt_warping import min_max_normalize

plt.rcParams.update({'font.size': 7,
                     'font.family': "Arial",
                     'axes.formatter.limits': (-4, 6),
                     'axes.formatter.use_mathtext': True})

data_delta = 10 # unit is second
distance_matrix = np.load(f"{project_root}/pipeline/cal_dwt_matrix/distance_matrix_1_2.npy", allow_pickle=True)
distance_matrix_norm = min_max_normalize(distance_matrix)
num_rows, num_cols = distance_matrix_norm.shape

selected_square = min(num_rows, num_cols)
num_rows, num_cols = selected_square, selected_square
distance_matrix_norm = distance_matrix_norm[:selected_square, :selected_square]

fig = plt.figure(figsize=(5.5, 5))
gs = gridspec.GridSpec(1, 2, width_ratios=[30, 1])

ax = plt.subplot(gs[0])
colorbar_ax = plt.subplot(gs[1])

h = sns.heatmap(distance_matrix_norm, annot=False, ax=ax, cbar_ax=colorbar_ax, zorder=1)



max_len = min(num_rows, num_cols)
ax.plot([0, max_len], [0, max_len], color='white', linestyle='--', linewidth=1)


# Put origin (0,0) at lower-left
ax.invert_yaxis()

interveal = 1800 / 10  # 1 hour / 10 s delta gap
locations = np.arange(0, num_cols, interveal)
labels = [i / 360 for i in locations]
ax.set_xticks(locations, labels=labels, rotation=0)
locations = np.arange(0, num_rows, interveal)
labels = [i / 360 for i in locations]
ax.set_yticks(locations, labels=labels)


ax.set_xlabel("Input DF1 Length [hour]", weight='bold')
ax.set_ylabel("Input DF2 Length [hour]", weight='bold')

colorbar_ax.set_ylabel("Normalized DWT Distance", rotation=90, weight="bold")

plt.tight_layout()
plt.savefig(f"./psd_slope_ILL.png", dpi=600, transparent=True)
plt.show()
