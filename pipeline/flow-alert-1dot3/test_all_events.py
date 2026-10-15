#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-18T15:13:51
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import platform
import argparse

import numpy as np
import pandas as pd
from obspy import UTCDateTime, read

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
from func.flow_bench.unique_identifier import build_identifier
from func.toolkit.xlsx_to_txt import xlsx2txt
from func.seismic.denoising import denoise_st


# add Flow-Alert func
if platform.system() == "Darwin":
    project_root = Path("/Users/qizhou/#python/Flow-Alert")
elif platform.system() == "Linux":
    project_root = Path("/storage/vast-gfz-hpc-01/home/qizhou/3paper/Flow_Alert")
else:
    raise ValueError(f"Unknow platform: {platform.system()}")
sys.path.insert(0, str(project_root))
import torch  # type: ignore


# import the custom functions
from functions.model.interface_model import FlowAlert  # type: ignore
from functions.warning_strategy.calculate_inference_matrix import inference_matrix  # type: ignore
from functions.data_process.cross_catchments_inference import find_max_amp_time  # type: ignore
from functions.toolkit.multi_process_archive import dump_as_row  # type: ignore
from functions.toolkit.synthetic_data import synthetic_stream  # type: ignore
from functions.seismic.plot_obspy_st import plot_amp_psd_pro  # type: ignore


def main(event_id, extra_time=24):  # run 24 hours data
    # region config
    if platform.system() == "Darwin":
        project_root = Path("/Users/qizhou/#python/Flow-Bench-geo")
    elif platform.system() == "Linux":
        project_root = Path("/storage/vast-gfz-hpc-01/home/qizhou/3paper/Flow-Bench-geo")
    else:
        raise ValueError(f"Unknow platform: {platform.system()}")

    fb_version = "v2dot1dot5"
    fmt = "%Y-%m-%dT%H:%M:%S"
    sub_window_size = 60  # unit by second
    window_overlap = 0.5
    model_version = "v1dot3model"
    model_type = "LSTM"
    identifier = build_identifier(version=fb_version, fmt=fmt)
    # endregion

    # region
    # load the FlowBench class
    fb = FlowBench(version=fb_version)
    seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)  # event start and end time

    # request one evnet
    f_min = 1
    f_max = min(25, float(seis_meta["seis_sampling_rate"][event_id]) / 2)

    # STA/LTA based event time
    starttime = event_meta.iloc[event_id, 0]  # type: ignore
    endtime = event_meta.iloc[event_id, 1]  # type: ignore
    mid_time = UTCDateTime(starttime) + float(UTCDateTime(endtime) - UTCDateTime(starttime)) / 2

    # longer time for testing
    starttime = UTCDateTime(mid_time) - extra_time / 2 * 3600
    starttime = starttime.strftime(fmt)
    endtime = UTCDateTime(mid_time) + extra_time / 2 * 3600
    endtime = endtime.strftime(fmt)

    # use the cahe methods
    cache_st_cooked = Path(project_root) / f"data/cache/cache_st_cooked/{identifier[event_id]}.mseed"
    cache_st_cooked.parent.mkdir(parents=True, exist_ok=True)
    if cache_st_cooked.exists():
        st_cooked = read(cache_st_cooked)
    else:
        try:
            # load the time
            st_raw, st_cooked = fb.request_one_seis_event(
                event_id=event_id,
                starttime=starttime,
                endtime=endtime,
                buffer_hour=0,
                f_min=f_min,
                f_max=f_max,
            )
        except Exception as e:
            print(e)
            # load the time
            st_raw, st_cooked = fb.request_one_seis_event(
                event_id=event_id,
                starttime=None,
                endtime=None,
                buffer_hour=3,
                f_min=f_min,
                f_max=f_max,
            )

        if seis_meta["seis_cat"][event_id] in ["Goulinping"]:
            st_cooked = synthetic_stream(
                # raw obspy stream, unit by counts
                st_raw=st_cooked,
                # for pading
                left_pad=1800,
                left_slice=60,
                right_pad=1800,
                right_slice=60,
                # random seed
                seed=1234,
            )

        st_cooked.write(cache_st_cooked, format="MSEED")

    # endregion

    # region
    # only select 2 hours before the events and 2 hour after the events
    input_xlsx_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{fb_version}.xlsx"
    output_txt_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{fb_version}.txt"
    column_s, column_e = 15, 17
    df = xlsx2txt(input_xlsx_path, output_txt_path, column_s, column_e)
    starttime = df.iloc[event_id, 0]  # this is fro STA/LTA ref
    endtime = df.iloc[event_id, 1]

    st_cooked = st_cooked.trim(
        # make sure there are 64 minutes data before the STA/LTA event start
        UTCDateTime(df.iloc[event_id, 0]) - 65 * 60,
        # stop the traces at the STA/LTA ref time
        UTCDateTime(df.iloc[event_id, 1]),
    )
    # endregion

    print(st_cooked[0].stats)  # type: ignore
    # sys.exit()  # for archive the data
    ###
    ### prediction
    # flow alert model
    output_dir = Path(project_root) / "data/cache/flow-alert-1dot3"
    output_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(device)

    cache_pro = Path(project_root) / f"data/cache/flow-alert-1dot3/pro/{identifier[event_id]}_pro.txt"
    cache_pro.parent.mkdir(parents=True, exist_ok=True)
    if cache_pro.exists():
        model_output = np.array(pd.read_csv(cache_pro, header=0))
    else:
        flow_alert = FlowAlert(
            model_type,
            model_version,
            st=st_cooked.copy(),
            output_path=output_dir,
            sub_window_size=sub_window_size,
            window_overlap=window_overlap,  # type: ignore
            clip_anomaly=True,
            num_cpus=1,
        )
        flow_alert.model_config()
        model_list = flow_alert.load_model()

        feature_arr = flow_alert.prepare_feature()
        model_output = flow_alert.make_prediction(tested_model=model_type)

        # region
        # save prediction results
        df = pd.DataFrame(feature_arr)
        feature_path = Path(project_root) / f"data/cache/flow-alert-1dot3/feat/{identifier[event_id]}_feat.txt"
        feature_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(feature_path, index=False)

        # save prediction results
        header = ["time_stamps", "time_window_start"] + [f"pro{i}" for i in range(9)] + ["pro_mean", "pro_ci"]
        df = pd.DataFrame(model_output, columns=header)
        df.to_csv(cache_pro, index=False)
        # endregion

    # statistic
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)
    sta_s = event_meta.iloc[event_id, 0]  # type: ignore
    sta_e = event_meta.iloc[event_id, 1]  # type: ignore

    low_sampling_rate, denoised_st = denoise_st(
        st=st_cooked.copy(),
        window_size=10,
        window_overlap=0,
        denoising_method="RMS",
        fmt="%Y-%m-%dT%H:%M:%S",
    )
    benchmark_time = find_max_amp_time(st=denoised_st, sta_s=sta_s, sta_e=sta_e, least_time=10)  # type: ignore
    # benchmark_time = sta_s  # overwrite the previous benchmark time

    (
        detection_type,
        first_detection,
        first_detection_str,
        increased_warning_time,
        false_detection,
        false_detection_ratio,
    ) = inference_matrix(
        array_temp=model_output,
        benchmark_time=benchmark_time,
        event_start=sta_s,
        event_end=sta_e,
        pro_epsilon=0.5,
        buffer1=0,
        buffer2=0.5,
    )

    # dump the results
    output_dir = Path(project_root) / "data/cache/flow-alert-1dot3"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_name = "inference-Non-ILL-event"
    variable_str = identifier[event_id]
    record = [
        detection_type,
        first_detection_str,
        benchmark_time,
        increased_warning_time,
        false_detection,
        false_detection_ratio,
    ]
    dump_as_row(output_dir, output_name, variable_str, *record)

    # plot
    note = (
        f"Detection Type: {detection_type},\n"
        f"Benchmark time (max amp. time) t1: {benchmark_time},\n"
        f"First Detection Time (pro >= 0.5) t2: {first_detection_str}, \n"
        f"Increased Warning Time (t1 - t2): {increased_warning_time} [seconds], \n"
        f"False Detection Ratio: {false_detection_ratio}, \n"
    )
    plot_amp_psd_pro(
        benchmark_time=benchmark_time,
        first_detection_str=first_detection_str,
        st=st_cooked.copy(),
        array_temp=model_output,
        output_path=output_dir,
        output_format=variable_str,
        note=note,
        f_min=f_min,
        f_max=f_max,
        time_markers=[sta_s, sta_e],
        time_markers_label=[f"t_s: {sta_s}", f"t_e: {sta_e}"],
        st_amp=denoised_st.copy(),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event_id", type=int, default=59)
    args = parser.parse_args()

    main(event_id=args.event_id)
