#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-18T15:42:25
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import platform
import argparse

import pandas as pd
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
from func.download.seis import load_raw_glic
from func.seismic.remove_response import cooking_recipe


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


def main(seis_station, julday1=171, julday2=201):  # run 24 hours data
    # region config
    if platform.system() == "Darwin":
        project_root = Path("/Users/qizhou/#python/Flow-Bench-geo")
    elif platform.system() == "Linux":
        project_root = Path("/storage/vast-gfz-hpc-01/home/qizhou/3paper/Flow-Bench-geo")
    else:
        raise ValueError(f"Unknow platform: {platform.system()}")

    sub_window_size = 60  # unit by second
    window_overlap = 0.5
    model_version = "v1dot3model"
    model_type = "LSTM"
    f_min, f_max = 1, 25
    # endregion

    for julday in range(julday1, julday2):
        starttime = UTCDateTime(year=2016, julday=julday)
        endtime = UTCDateTime(year=2016, julday=julday) + 3600 * 24

        st_raw, inv_or_paz = load_raw_glic(
            # catchment meta
            continent="Asia",
            seis_cat="Bothekoshi",
            # seismic meta
            seis_client="GEOFON",
            seis_network="XN",
            seis_station=seis_station,
            seis_location="",
            seis_channel="HHZ",
            # response meta
            seis_response="xml",
            sensor_type="",
            # event meta
            starttime=starttime,
            endtime=endtime,
            # default params
            save_st=False,
            save_inv=True,
            local_dir="data/seis_raw",
        )
        st_cooked = cooking_recipe(st=st_raw, inv_or_paz=inv_or_paz, f_min=f_min, f_max=f_max)
        print(st_cooked[0].stats)  # type: ignore

        ### prediction
        # flow alert model
        output_dir = Path(project_root) / "data/cache/flow-alert-1dot3/Bhotekoshi"
        output_dir.mkdir(parents=True, exist_ok=True)

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print(device)

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
        feature_path = Path(project_root) / f"data/cache/flow-alert-1dot3/feat/{seis_station}_{julday:03d}_feat.txt"
        feature_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(feature_path, index=False)

        # save prediction results
        header = ["time_stamps", "time_window_start"] + [f"pro{i}" for i in range(9)] + ["pro_mean", "pro_ci"]
        df = pd.DataFrame(model_output, columns=header)
        cache_pro_path = Path(project_root) / f"data/cache/flow-alert-1dot3/pro/{seis_station}_{julday:03d}_pro.txt"
        cache_pro_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_pro_path, index=False)
        # endregion


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seis_station", type=str, default="NEP08")
    args = parser.parse_args()

    main(seis_station=args.seis_station)
