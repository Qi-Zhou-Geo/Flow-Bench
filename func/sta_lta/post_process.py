#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-10T10:51:03
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission


import matplotlib.pyplot as plt

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
from func.seismic.plot_obspy_st import time_series_plot


def plot_sta_lta(st_file_list, 
                 time_markers,
                 time_markers_label,
                 f_min, f_max,
                 ratio_on, ratio_off,
                 output_path, output_name):
    
    fig, axes = time_series_plot(st_file_list, time_markers=time_markers, time_markers_label=time_markers_label)
    y_label = ["Amplitude\n[m/s]", "STA/LTA Ratio\n[forward]", "STA/LTA Ratio\n[backward]"]

    for idx, (ax, label) in enumerate(zip(axes, y_label)):
        ax.set_ylabel(f"{label}", fontweight='bold')

        if idx == 0:
            ax.set_title(label=f"f_min={f_min}, f_max={f_max}"
                               f"\nratio_on={ratio_on}, ratio_off={ratio_off}", fontsize=7, fontweight='bold')
        else:
            ax.axhline(y=ratio_on, color="red", ls="--", lw=1, alpha=0.5, zorder=5, label=f"ratio_on={ratio_on}")
            ax.axhline(y=ratio_off, color="green", ls="-", lw=1, alpha=0.5,  zorder=4, label=f"ratio_off={ratio_off}")
            ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.subplots_adjust(wspace=0.1, hspace=0.3)
    
    png_path = Path(output_path) / output_name
    png_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(png_path, dpi=600, transparent=False)
    plt.close(fig)

