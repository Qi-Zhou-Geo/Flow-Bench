#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-18T16:33:48
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission


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

fb = FlowBench(version="v2dot1dot2")
# load the meta
seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
event_meta = fb.get_metadata(meta_type="event", print_meta=False)

for event_id in range(len(seis_meta)):
    try:
        st_raw, st_cooked = fb.request_one_seis_event(event_id=event_id)
        sta_lta_timing = fb.get_event_t(st=st_cooked, show_plot=True, save_plot=True, event_id=event_id)
    except Exception as e:
        print(event_id, e)
