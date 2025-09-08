#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2025-05-12
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>


plt.rcParams.update( {'font.size':7,
                      'font.family': "Arial",
                      'axes.formatter.limits': (-4, 6),
                      'axes.formatter.use_mathtext': True} )

def plot_noise_model(ax, noise_model="Wolin2019", color="red"):

    if noise_model == "Peterson1993":
        with np.load(f"{project_root}/data/noise_model/low-noise-model-Peterson1993.npz") as f:
            periods_l, psd_lnm = f["periods"], f["lnm"]
            # low noise model, for information on New High/Low Noise Model see [Peterson1993].
            ax.plot(1 / periods, psd_lnm, color=color, lw=1.5, ls="--", zorder=5, label="Low noise model")

        with np.load(f"{project_root}/data/noise_model/high-noise-model-Peterson1993.npz") as f:
            periods_h, psd_hnm = f["periods"], f["hnm"]
            # high noise model, for information on New High/Low Noise Model see [Peterson1993].
            ax.plot(1 / periods, psd_hnm, color=color, lw=1.5, ls="-", zorder=5, label="High noise model")

    if noise_model == "Wolin2019":
        from scipy.signal import savgol_filter

        df = pd.read_csv(f"{project_root}/data/noise_model/low‐noise-model-Wolin2019.csv", header=0)
        periods_l, psd_lnm = 1/df.iloc[:, 0], df.iloc[:, 1]
        psd_lnm = savgol_filter(psd_lnm, window_length=15, polyorder=2)

        df = pd.read_csv(f"{project_root}/data/noise_model/high‐noise-model-Wolin2019.csv", header=0)
        periods_h, psd_hnm = 1/df.iloc[:, 0], df.iloc[:, 1]
        psd_hnm = savgol_filter(psd_hnm, window_length=15, polyorder=2)

    ax.plot(1 / periods_l, psd_lnm, color=color, lw=1.5, ls="--", zorder=2, label="Low noise model")
    ax.plot(1 / periods_h, psd_hnm, color=color, lw=1.5, ls="--", zorder=2, label="High noise model")

    return ax
