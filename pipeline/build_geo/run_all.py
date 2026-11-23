#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-02T22:18:00
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
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

# import custom func.
from func.flow_bench.FlowBench import FlowBenchHydro

version = "essd"
fh = FlowBenchHydro(version=version)
seis_meta = fh.seis_meta
dem_meta = fh.dem_meta

# rebuild the summary for this batch, starting with the first successful result
write_header = True
hydrogeomorphic_output_path = fh.hydro_cooked_dir / "hydrogeomorphic_by_outlet.txt"
hydrogeomorphic_output_path.parent.mkdir(parents=True, exist_ok=True)

# delete it when run it at the first time
if hydrogeomorphic_output_path.exists():
    hydrogeomorphic_output_path.unlink(missing_ok=True)


unique_catchment_outlet_pair = set()

## TODO: Loop the catchment dimension
for seis_cat in seis_meta["seis_cat"].unique():
    all_events_id = np.where(seis_meta["seis_cat"] == seis_cat)[0]

    ## TODO: Loop the outlet dimension
    for id in all_events_id:
        ##
        outlet_lat = dem_meta["dem_outlet_lat"].iloc[id]
        outlet_lon = dem_meta["dem_outlet_lon"].iloc[id]
        pair = (seis_cat, outlet_lat, outlet_lon)

        if pair in unique_catchment_outlet_pair:
            # this catchment and outlet have already been calculated
            continue

        # note from QZ, Last modified: 2026-11-02T22:05:06
        # for a given catchment with mutiple stations,

        # if the event runs in the same channel (with same outlet),
        # only the first  station will be used.

        # else, the new catchment and outlet will be calculated.

        fh.download_dem(id)  # (1) download the dem
        fh.process_catchment(id)  # (2) extract the streams
        fh.plot_overview(id)  # (3) plot and check the results
        df = fh.calculate_statistic(id)  # (4) do statistic

        # (5) archive the results
        if write_header is True:
            mode = "w"
        else:
            mode = "a"

        df.to_csv(hydrogeomorphic_output_path, mode=mode, header=write_header, index=False)
        write_header = False

        unique_catchment_outlet_pair.add(pair)
        print(f"Done: {pair}\n")
