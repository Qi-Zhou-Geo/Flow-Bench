#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-10T17:01:31
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz-potsdam.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd

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


def load_plot_single_event(event_id, identifier, ax, zorder, color, label):

    # load the data
    cache_name = identifier[event_id]
    cache_dir = Path(project_root) / f"data/cache/fitted_psd_freq/{cache_name}.npz"
    temp = np.load(cache_dir, allow_pickle=True)
    freq = temp["freq"]
    psd = temp["psd"]
    psd_unit = temp["psd_unit"]

    # plot it
    ax.plot(freq, psd, alpha=0.5, lw=1, zorder=zorder, color=color, label=label)
    ax.set_xscale("log")
    ax.set_xlim(1, 50)
    ax.set_ylim(-180, -80)

    return ax
