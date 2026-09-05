#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-03T15:37:08
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import argparse
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
from func.toolkit.xlsx_to_txt import xlsx2txt

version = "v2dot1dot5"
fb = FlowBench(version=version)
# load the meta
seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
event_meta = fb.get_metadata(meta_type="event", print_meta=False)


input_xlsx_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{version}.xlsx"
output_txt_path = Path(project_root) / f"data/event_catalog/Flow_Bench_Catalog_{version}.txt"
column_s, column_e = 15, 17
df = xlsx2txt(input_xlsx_path, output_txt_path, column_s, column_e)

f_min = 1
f_max = 10
thr_on = 0.3
thr_off = 0.3


# for event_id in range(len(seis_meta)):
def main(event_id=0):

    try:
        # load the seismic data
        st_raw, st_cooked = fb.request_one_seis_event(
            event_id=event_id,
            f_min=f_min,
            f_max=f_max,
        )

        if df.iloc[event_id, 0] == "do-not-need" and df.iloc[event_id, 1] == "do-not-need":
            pass
        else:
            starttime = df.iloc[event_id, 0]
            endtime = df.iloc[event_id, 1]
            st_cooked = st_cooked.trim(UTCDateTime(starttime), UTCDateTime(endtime))

        # do the STA/LTA
        sta_lta_timing = fb.get_event_t(
            st=st_cooked,
            show_plot=True,
            save_plot=True,
            event_id=event_id,
            thr_on=thr_on,
            thr_off=thr_off,
            f_min=f_min,
            f_max=f_max,
        )

        print(sta_lta_timing)
    except Exception as e:  # noqa: BLE001
        print(event_id, e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("event_id", type=int)
    args = parser.parse_args()

    main(event_id=args.event_id)
