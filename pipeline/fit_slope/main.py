#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-02T15:17:43
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import argparse
import numpy as np

import matplotlib.pyplot as plt
from matplotlib import gridspec

from obspy import UTCDateTime

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
from func.flow_bench.FlowBench import FlowBenchSeis
from func.color_of_noise.psd_slope import plot_fitting, convert_st2psd
from data.noise_model.visualize_noise_model import plot_Wolin2019_model
from func.toolkit.mpi_archive import dump_as_row
from func.flow_bench.unique_identifier import build_identifier


def main(event_id, st, f_min, f_max, output_name, fmt="%Y-%m-%dT%H:%M:%S"):

    stats = st[0].stats

    # (1) fit the PSD slope
    # note, the st should be only inbclude the event period
    tr = st.copy()
    freq, psd, psd_unit = convert_st2psd(st=tr)

    mask = (freq >= f_min) & (freq <= f_max)
    freq_selected = freq[mask]
    psd_selected = psd[mask]

    # (2) save the processed psd-freq
    output_dir = Path(project_root) / f"data/cache/fitted_psd_freq/{output_name}.npz"
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        file=output_dir,
        # data
        output_name=output_name,
        freq=freq_selected,
        psd=psd_selected,
        psd_unit=psd_unit,
    )

    # (3) plot the fitted psd slope
    fig = plt.figure(figsize=(5, 5))
    gs = gridspec.GridSpec(1, 1)

    ax = plt.subplot(gs[0])
    sta_s = stats.starttime.strftime(fmt)
    sta_e = stats.endtime.strftime(fmt)
    sps = stats.sampling_rate
    title_text = f"Data: {sta_s} to {sta_e}, SPS={sps}"
    ax.set_title(title_text, fontsize=7, fontweight="bold")

    plot_Wolin2019_model(ax, color="#D9544D", plot_type="area")
    record = plot_fitting(ax, freq_selected, psd_selected, confidence_interval=0.95)

    ax.set_xlabel("Frequency [Hz]", fontweight="bold")
    ax.set_ylabel("Power Spectral Density [dB]", fontweight="bold")

    plt.tight_layout()
    png_dir = Path(project_root) / f"data/cache/fitted_psd_freq_plot/{output_name}.png"
    png_dir.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(png_dir, dpi=600, transparent=False)
    plt.close(fig=fig)

    # (4) dump the fited slope results
    txt_path = Path(current_dir)
    txt_path.mkdir(parents=True, exist_ok=True)
    txt_name = "fitted_slope.txt"
    variable_str = output_name  # meta data
    # record is [beta, beta_CI[0], beta_CI[1], intercept, s_residual, r_squared, p_value, peak_freq]
    dump_as_row(txt_path, txt_name, variable_str, *record)


if __name__ == "__main__":
    # sinfo -n node[501-514] -N --Format="Nodelist,CPUsState,AllocMem,Memory,GresUsed,Gres"
    parser = argparse.ArgumentParser(description="input parameters")
    parser.add_argument("--version", default="v2dot1dot5", type=str)
    parser.add_argument("--event_id", default=0, type=int)
    args = parser.parse_args()

    # load the meta and 3 hours more data
    fb = FlowBenchSeis(version=args.version)
    seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)

    # if seis_meta["seis_sampling_rate"][args.event_id] >= 100:
    #     f_min, f_max = 1, 50
    # else:
    #     f_min, f_max = 1, float(seis_meta["seis_sampling_rate"][args.event_id]) / 2
    f_min, f_max = 1, float(seis_meta["seis_sampling_rate"][args.event_id]) / 2

    st_raw, st_cooked = fb.request_one_seis_event(
        event_id=args.event_id,
        starttime=None,
        endtime=None,
        buffer_hour=3,
        f_min=f_min,
        f_max=f_max,
    )

    # trim the event
    st_cooked.trim(
        UTCDateTime(event_meta["event_time_s"][args.event_id]),
        UTCDateTime(event_meta["event_time_e"][args.event_id]),
    )

    identifier = build_identifier(version=args.version, fmt="%Y-%m-%dT%H:%M:%S")
    output_name = identifier[args.event_id]
    main(args.event_id, st=st_cooked, f_min=f_min, f_max=f_max, output_name=output_name, fmt="%Y-%m-%dT%H:%M:%S")
    print(f"Done! {args.event_id}\n\n")
