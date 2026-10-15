#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-15T14:11:40
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import argparse
import numpy as np

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
from func.flow_bench.FlowBench import FlowBench
from func.seismic.denoising import denoise_st
from func.flow_bench.unique_identifier import build_identifier
from func.toolkit.xlsx_to_txt import xlsx2txt


def cache_events(
    event_id,
    version="v2dot1dot5",
    window_size=10,
    window_overlap=0,
    denoising_method="RMS",
    fmt="%Y-%m-%dT%H:%M:%S",
):

    # load the class
    fb = FlowBench(version=version)
    seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)

    # request one evnet
    f_min = 1
    f_max = min(25, float(seis_meta["seis_sampling_rate"][event_id]) / 2)

    # load the time
    st_raw, st_cooked = fb.request_one_seis_event(
        event_id=event_id,
        starttime=None,
        endtime=None,
        buffer_hour=3,
        f_min=f_min,
        f_max=f_max,
    )

    # trim the event based on the STA/LTA ref time
    input_xlsx_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{version}.xlsx"
    output_txt_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{version}.txt"
    column_s, column_e = 15, 17
    df = xlsx2txt(input_xlsx_path, output_txt_path, column_s, column_e)

    starttime = df.iloc[event_id, 0]
    endtime = df.iloc[event_id, 1]
    st_cooked = st_cooked.trim(UTCDateTime(starttime), UTCDateTime(endtime))

    # denoise
    st_copy = st_cooked.copy()
    low_sampling_rate, denoised_st = denoise_st(
        st=st_copy,
        window_size=window_size,
        window_overlap=window_overlap,
        denoising_method=denoising_method,
        fmt=fmt,
    )

    # save to local
    identifier = build_identifier(version=version, fmt=fmt)
    output_name = identifier[event_id]
    npz_path = Path(project_root) / f"data/cache/denoised_st/{output_name}.npz"
    npz_path.parent.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        file=npz_path,
        f_min=f_min,
        f_max=f_max,
        starttime=denoised_st[0].stats.starttime.strftime(fmt),  # type: ignore
        denoised_st=denoised_st[0].data,  # type: ignore
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event_id", type=int, default=60)
    args = parser.parse_args()

    cache_events(
        event_id=args.event_id,
        version="v2dot1dot5",
        window_size=10,
        window_overlap=0,
        denoising_method="RMS",
        fmt="%Y-%m-%dT%H:%M:%S",
    )
