#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-10-17T15:26:50
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import shutil
import numpy as np
import pandas as pd
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

# import custom func.
from func.download.dem_copernicus import download_dem_from_copernicus
from func.hydro.extract_geo import geo_extracter

from func.hydro.geo_tool import project_dem, point2gpd
from func.hydro.geo_plot import plot_catchment
from func.hydro.geo_stastic import calculate_catchment
from func.flow_bench.FlowBench import FlowBench
from func.flow_bench.unique_identifier import build_identifier


# region >> input params
wbt_threshold_default = 500
wbt_threshold_dict = {
    "Casamicciola": 5,
    "Chalk Cliffs": 5,
    "Hsiaolin": 100,
}

snap_dist_default = 0.001
snap_dist_dict = {
    "Ergou": 0.03,
    "Huangbengliu": 0.03,
    "Museum Fire": 0.03,
    "Gorkha": 0.03,
    "Montecito": 0.03,
    "Bothekoshi": 0.03,
    "Tbilisa": 0.01,
    "Yanmen": 0.03,
}

version = "essd"
num_d = 1  # for channel slope of debris-flow channel
# endregion

# unique identifier for the all events
identifier = build_identifier(version=version, fmt="%Y-%m-%dT%H:%M:%S")
fb = FlowBench(version=version)
# load the meta
seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
dem_meta = fb.get_metadata(meta_type="dem", print_meta=False)

# rebuild the summary for this batch, starting with the first successful result
write_header = True
hydrogeomorphic_output_path = Path(project_root) / "cache/hydrogeomorphic_by_outlet.txt"
hydrogeomorphic_output_path.parent.mkdir(parents=True, exist_ok=True)
# delete it when run it at the first time
if hydrogeomorphic_output_path.exists():
    hydrogeomorphic_output_path.unlink(missing_ok=True)


unique_catchemnt_outlet_pair = set()
## TODO: Loop the catchment dimension
for seis_cat in seis_meta["seis_cat"].unique():
    all_events_id = np.where(seis_meta["seis_cat"] == seis_cat)[0]

    ## TODO: Loop the outlet dimension
    for id in all_events_id:
        ##
        outlet_lat = dem_meta["dem_outlet_lat"].iloc[id]
        outlet_lon = dem_meta["dem_outlet_lon"].iloc[id]
        pair = (seis_cat, outlet_lat, outlet_lon)

        if pair in unique_catchemnt_outlet_pair:
            # this catchment and outlet have already been calculated
            continue

        # note from QZ, Last modified: 2026-10-17T13:44:26
        # for a given catchment with mutiple stations,
        # if the event runs in the same channel (with same outlet),
        # only the first  station will be used.
        # else, the new catchment and outlet will be calculated.
        seis_sta_name = (
            f"{seis_meta['seis_network'].iloc[id]}-"
            f"{seis_meta['seis_station'].iloc[id]}-"
            f"{seis_meta['seis_channel'].iloc[id]}"
        )
        seis_lon, seis_lat = seis_meta["seis_lon"][id], seis_meta["seis_lat"][id]

        # main loop
        wbt_threshold = wbt_threshold_dict.get(seis_cat, wbt_threshold_default)
        snap_dist = snap_dist_dict.get(seis_cat, snap_dist_default)

        # region (1) download the dem
        dem_provider = dem_meta["dem_provider"][id]
        dem_resolution = int(dem_meta["dem_resolution"][id])  # unit is m
        dem_range = (
            # do not change the order
            float(dem_meta["dem_west_lon"][id]),
            float(dem_meta["dem_south_lat"][id]),
            float(dem_meta["dem_east_lon"][id]),
            float(dem_meta["dem_north_lat"][id]),
        )

        raw_dem_path = Path(project_root) / f"data/hydro_raw/{seis_cat}/{seis_cat}_{dem_provider}_{dem_resolution}m.tif"
        if raw_dem_path.exists():
            print(f"Use the exist DEM:\n{raw_dem_path}\n")
        else:
            raw_dem_path = download_dem_from_copernicus(
                version=version,
                seis_cat=seis_cat,
                dem_provider=dem_provider,
                dem_resolution=dem_resolution,
                dem_range=dem_range,
            )
        # endregion

        output_dir = Path(project_root) / f"data/hydro_cooked/{seis_cat}/outlet_{id:03d}"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # region (2) extract the streams
        geo_extracter(
            dem_path=raw_dem_path,
            outlet_lon=outlet_lon,
            outlet_lat=outlet_lat,
            output_dir=output_dir,
            threshold=wbt_threshold,
            snap_dist=snap_dist,
            delete_cache=False,
        )
        # endregion

        # region (3) plot and check the results
        projected_dem_path = Path(output_dir) / f"{seis_cat}_{dem_resolution}_UTM.tif"
        projected_dem_path.parent.mkdir(parents=True, exist_ok=True)
        projected_dem_path = project_dem(
            dem_path=raw_dem_path,
            projected_dem_path=projected_dem_path,
            resolution=dem_resolution,
        )

        seismic_sta_path = Path(output_dir) / "seis_sta.shp"
        point2gpd(
            lon=seis_lon,  # float, unit by degree
            lat=seis_lat,  # float, unit by degree
            save_path=seismic_sta_path,
            crs="EPSG:4326",
        )

        catchment_path = Path(output_dir) / "catchment.shp"
        channel_path = Path(output_dir) / "main_df_channel.shp"

        outlet_path = Path(output_dir) / "outlet.shp"
        snapped_outlet_path = Path(output_dir) / "temp/snapped_outlet.shp"
        if snapped_outlet_path.exists():
            pass
        else:
            snapped_outlet_path = None

        head_path = None
        snapped_head_path = None

        png_path = Path(output_dir) / f"{seis_cat}_overview.png"

        fig, ax = plot_catchment(
            projected_dem_path=projected_dem_path,
            catchment_path=catchment_path,
            channel_path=channel_path,
            ##
            head_path=head_path,
            snapped_head_path=snapped_head_path,
            ##
            outlet_path=outlet_path,
            snapped_outlet_path=snapped_outlet_path,
            ##
            seismic_sta_path=seismic_sta_path,
            ##
            save_path=png_path,
            ##
            crs="EPSG:4326",  # WGS 84 longitude/latitude
            ##
            plot_elevation_legend=True,
        )
        plt.close(fig)
        # endregion

        # region (4) do statistic
        stations = [
            (seis_sta_name, seis_lon, seis_lat),  # add , as List[tuple]
        ]

        main_df_channel_path = Path(output_dir) / "main_df_channel.shp"
        main_df_channel_extend_path = Path(output_dir) / "main_df_channel_extend_5000m.shp"

        geometry, relief, station_metrics = calculate_catchment(
            projected_dem_path=projected_dem_path,
            catchment_path=catchment_path,
            main_df_channel_path=main_df_channel_path,
            main_df_channel_extend_path=main_df_channel_extend_path,
            stations=stations,
            n=num_d,
        )
        # endregion

        # region (5) archive the results
        geo_row = pd.Series(geometry).round(4).to_frame().T
        relief_row = pd.Series(relief).round(4).to_frame().T
        sta_row = station_metrics.reset_index(drop=True)
        df = pd.concat([geo_row, relief_row, sta_row], axis=1)

        df["seis_cat"] = seis_cat
        df["metadata_row"] = id
        df["identifier"] = identifier[id]
        df["dem_outlet_lat"] = outlet_lat
        df["dem_outlet_lon"] = outlet_lon

        if write_header is True:
            mode = "w"
        else:
            mode = "a"
        df.to_csv(hydrogeomorphic_output_path, mode=mode, header=write_header, index=False)
        write_header = False
        # endregion

        unique_catchemnt_outlet_pair.add(pair)
        print(f"Done: {pair}\n")
