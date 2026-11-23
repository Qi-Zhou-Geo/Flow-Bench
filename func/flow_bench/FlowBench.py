#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-02T22:11:47
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import shutil
import pandas as pd
from obspy import UTCDateTime

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
# for metadata
from func.toolkit.xlsx_to_txt import xlsx2txt

# for download
from func.download.seis_wrapper import all_seis_data, one_seis_event

# for STA/LTA
from func.seismic.denoising import denoise_st
from func.sta_lta.forward_backward import forward_backward_sta_lta
from func.sta_lta.post_process import plot_sta_lta, plot_sta_lta_psd

# for hydrogeomorphic
from config.wbt_params import load_wbt_params
from func.download.dem_copernicus import download_dem_from_copernicus

from func.hydro.extract_geo import geo_extracter
from func.hydro.geo_tool import project_dem, point2gpd

from func.hydro.geo_stastic import calculate_catchment

from func.hydro.geo_plot import plot_catchment


class FlowBenchSeis:
    def __init__(self, version):

        # model version, e.g., "v2dot1dot1"
        self.version = version

        # I/O dir
        self.project_root = project_root  # project root directory
        print(f"Note! Your working <project_root> is: {project_root}")

        # general parameters
        self.buffer_day = 1  # number of days before and after the event for data download
        self.buffer_hour = 3  # number of hours before and after the event for event-level analysis
        self.window_size = 10  # window length in seconds
        self.window_overlap = 0  # window overlap ratio; 0 means no overlap
        self.fmt = "%Y-%m-%dT%H:%M:%S"  # datetime string format

        # seismic preprocessing parameters
        self.f_min = 1  # lower cutoff frequency in Hz
        self.f_max = 25  # upper cutoff frequency in Hz

        # STA/LTA event timing parameters
        self.sta = 180  # short-term average window length in seconds
        self.lta = 1800  # long-term average window length in seconds
        self.thr_on = 0.2  # trigger-on threshold
        self.thr_off = 0.2  # trigger-off threshold
        self.min_event_duration = 60  # minimum event duration in seconds

    def get_metadata(self, meta_type, print_meta=True):

        meta_xlsx = Path(self.project_root) / f"data/event_catalog/Flow_Bench_Catalog_{self.version}.xlsx"
        meta_txt = Path(self.project_root) / f"data/event_catalog/Flow_Bench_Catalog_{self.version}.txt"

        # note you may check the column ID
        if meta_type == "all":
            column_s, column_e = 17, 18 + 1
        elif meta_type == "seis":
            column_s, column_e = 0, 11 + 1
        elif meta_type == "dem":
            column_s, column_e = 22, 30 + 1
        elif meta_type == "event":
            column_s, column_e = 17, 18 + 1
        else:
            raise ValueError(f"Unsupported meta_type: {meta_type}.\nYou may check the column ID at:\n{meta_xlsx}\n\n")

        df_meta = xlsx2txt(input_xlsx_path=meta_xlsx, output_txt_path=meta_txt, column_s=column_s, column_e=column_e)

        if print_meta is True:
            print(f"Flow-Bnech Metadata\nNum of rows: {len(df_meta.index)}\nName of columns: {df_meta.columns}\n\n")

        return df_meta

    def down_all_seis_data(self, buffer_day=None, data_source="FDSN"):

        # (1) load the meta
        seis_meta = self.get_metadata(meta_type="seis", print_meta=False)
        event_meta = self.get_metadata(meta_type="event", print_meta=False)

        # (2) check the parameters
        if buffer_day is None:
            buffer_day = self.buffer_day

        all_seis_data(
            seis_meta=seis_meta,
            event_meta=event_meta,
            buffer=buffer_day,
            data_source=data_source,
        )

    def request_one_seis_event(self, event_id, starttime=None, endtime=None, buffer_hour=None, f_min=None, f_max=None):

        # (1) load the meta
        seis_meta = self.get_metadata(meta_type="seis", print_meta=False)
        event_meta = self.get_metadata(meta_type="event", print_meta=False)

        # (2) check the parameters
        if buffer_hour is None:
            buffer_hour = self.buffer_hour

        if starttime is None:
            starttime = UTCDateTime(event_meta["event_time_s"][event_id]) - buffer_hour * 3600

        if endtime is None:
            endtime = UTCDateTime(event_meta["event_time_e"][event_id]) + buffer_hour * 3600

        if f_min is None:
            f_min = self.f_min

        if f_max is None:
            f_max = self.f_max

        # (3) request the data
        st_raw, st_cooked = one_seis_event(
            seis_meta=seis_meta,
            event_meta=event_meta,
            event_id=event_id,
            starttime=starttime,
            endtime=endtime,
            f_min=f_min,
            f_max=f_max,
        )

        return st_raw, st_cooked

    def get_event_t(
        self,
        # obspy stream
        st,
        # denoise
        window_size=None,
        window_overlap=None,
        denoising_method=None,
        # STA-LTA
        sta=None,
        lta=None,
        thr_on=None,
        thr_off=None,
        f_min=None,
        f_max=None,
        # default params
        smooth_sec=None,
        min_event_duration=None,
        # plot and save
        show_plot=True,
        save_plot=False,
        event_id=None,
    ):

        # (1) check the parameters
        # region
        if window_size is None:
            window_size = self.window_size

        if window_overlap is None:
            window_overlap = self.window_overlap

        if denoising_method is None:
            denoising_method = "RMS"

        if sta is None:
            sta = self.sta

        if lta is None:
            lta = self.lta

        if thr_on is None:
            thr_on = self.thr_on

        if thr_off is None:
            thr_off = self.thr_off

        if smooth_sec is None:
            pass

        if min_event_duration is None:
            min_event_duration = self.min_event_duration

        if f_min is None:
            f_min = self.f_min

        if f_max is None:
            f_max = self.f_max
        # endregion

        # (2) denoise it
        st_copy = st.copy()
        low_sampling_rate, denoised_st = denoise_st(
            st=st_copy,
            window_size=window_size,
            window_overlap=window_overlap,
            denoising_method=denoising_method,
            fmt=self.fmt,
        )

        # (3) apply the forward-backward STA/LTA
        sta_lta_timing = forward_backward_sta_lta(
            # obspy stream
            st=denoised_st,
            # STA-LTA
            sta=sta,
            lta=lta,
            thr_on=thr_on,
            thr_off=thr_off,
            # default params
            smooth_sec=smooth_sec,
            min_event_duration=min_event_duration,
            fmt=self.fmt,
        )

        if show_plot is True:
            png_path = Path(self.project_root) / "plots/STA-LTA"
            stats = denoised_st[0].stats  # type: ignore

            t1 = UTCDateTime(stats.starttime).strftime(self.fmt)
            t2 = UTCDateTime(stats.starttime).strftime(self.fmt)
            if event_id is None:
                png_name = f"{t1}_to_{t2}"
            else:
                png_name = f"{event_id:03d}_{t1}_to_{t2}"

            plot_sta_lta(
                st=denoised_st,
                sta_lta_timing=sta_lta_timing,
                # STA-LTA
                sta=sta,
                lta=lta,
                thr_on=thr_on,
                thr_off=thr_off,
                # default params
                f_min=f_min,
                f_max=f_max,
                # show and save
                show_plot=show_plot,
                save_plot=save_plot,
                png_path=png_path,
                png_name=png_name,
            )

            if save_plot is True:
                png_name = f"{event_id:03d}_{t1}_to_{t2}_psd.png"
                plot_sta_lta_psd(
                    st=st.copy(),
                    sta_lta_timing=sta_lta_timing,
                    x_interval=2,
                    png_path=png_path,
                    png_name=png_name,
                )

        return sta_lta_timing


class FlowBenchHydro:
    def __init__(self, version):

        # model version
        self.version = version

        # I/O dir
        self.project_root = project_root  # project root directory
        print(f"Note! Your working <project_root> is: {project_root}")

        self.hydro_raw_dir = Path(self.project_root) / "data/hydro_raw"
        self.hydro_cooked_dir = Path(self.project_root) / "data/hydro_cooked"

        # load the meta once, same catalog and column IDs as the seismic class
        fb_seis = FlowBenchSeis(version=version)
        self.seis_meta = fb_seis.get_metadata(meta_type="seis", print_meta=False)
        self.dem_meta = fb_seis.get_metadata(meta_type="dem", print_meta=False)

        # general parameters
        self.num_d = 1  # for channel slope of debris-flow channel
        self.channel_extend = 5000  # channel extension length in m
        self.delete_cache = False  # delete the WhiteboxTools cache after stream extraction

        # WhiteboxTools parameters, per catchment (fallback to the default)
        (
            self.wbt_threshold_default,
            self.wbt_threshold_dict,
            self.snap_dist_default,
            self.snap_dist_dict,
        ) = load_wbt_params()

    def get_raw_dem_path(self, event_id):

        seis_cat = self.seis_meta["seis_cat"].iloc[event_id]
        dem_provider = self.dem_meta["dem_provider"].iloc[event_id]
        dem_resolution = int(self.dem_meta["dem_resolution"].iloc[event_id])  # unit is m

        raw_dem_path = self.hydro_raw_dir / f"{seis_cat}/{seis_cat}_{dem_provider}_{dem_resolution}m.tif"

        return raw_dem_path

    def get_output_dir(self, event_id):

        seis_cat = self.seis_meta["seis_cat"].iloc[event_id]
        output_dir = self.hydro_cooked_dir / f"{seis_cat}/outlet_{event_id:03d}"

        return output_dir

    def get_projected_dem_path(self, event_id):

        seis_cat = self.seis_meta["seis_cat"].iloc[event_id]
        dem_resolution = int(self.dem_meta["dem_resolution"].iloc[event_id])

        projected_dem_path = self.get_output_dir(event_id) / f"{seis_cat}_{dem_resolution}_UTM.tif"

        return projected_dem_path

    def download_dem(self, event_id):

        raw_dem_path = self.get_raw_dem_path(event_id)

        # use the existing DEM or download it
        if raw_dem_path.exists():
            print(f"Use the exist DEM:\n{raw_dem_path}\n")
        else:
            raw_dem_path = download_dem_from_copernicus(
                version=self.version,
                seis_cat=self.seis_meta["seis_cat"].iloc[event_id],
                dem_provider=self.dem_meta["dem_provider"].iloc[event_id],
                dem_resolution=int(self.dem_meta["dem_resolution"].iloc[event_id]),
                dem_range=(
                    # do not change the order
                    float(self.dem_meta["dem_west_lon"].iloc[event_id]),
                    float(self.dem_meta["dem_south_lat"].iloc[event_id]),
                    float(self.dem_meta["dem_east_lon"].iloc[event_id]),
                    float(self.dem_meta["dem_north_lat"].iloc[event_id]),
                ),
            )

        return raw_dem_path

    def process_catchment(
        self,
        event_id,
        wbt_threshold=None,
        snap_dist=None,
        delete_cache=None,
    ):
        """raw DEM >> streams, catchment, outlet, projected DEM"""

        seis_cat = self.seis_meta["seis_cat"].iloc[event_id]
        dem_resolution = int(self.dem_meta["dem_resolution"].iloc[event_id])

        # (1) check the parameters
        if wbt_threshold is None:
            wbt_threshold = self.wbt_threshold_dict.get(seis_cat, self.wbt_threshold_default)

        if snap_dist is None:
            snap_dist = self.snap_dist_dict.get(seis_cat, self.snap_dist_default)

        if delete_cache is None:
            delete_cache = self.delete_cache

        raw_dem_path = self.get_raw_dem_path(event_id)
        if raw_dem_path.exists() is False:
            raise FileNotFoundError(f"Run download_dem first, missing:\n{raw_dem_path}")

        # (2) clean the output dir
        output_dir = self.get_output_dir(event_id)
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # (3) extract the streams and project the DEM
        geo_extracter(
            dem_path=raw_dem_path,
            outlet_lon=self.dem_meta["dem_outlet_lon"].iloc[event_id],
            outlet_lat=self.dem_meta["dem_outlet_lat"].iloc[event_id],
            output_dir=output_dir,
            threshold=wbt_threshold,
            snap_dist=snap_dist,
            delete_cache=delete_cache,
        )

        projected_dem_path = project_dem(
            dem_path=raw_dem_path,
            projected_dem_path=self.get_projected_dem_path(event_id),
            resolution=dem_resolution,
        )

        return projected_dem_path

    def plot_overview(self, event_id):

        seis_cat = self.seis_meta["seis_cat"].iloc[event_id]
        output_dir = self.get_output_dir(event_id)

        projected_dem_path = self.get_projected_dem_path(event_id)
        if projected_dem_path.exists() is False:
            raise FileNotFoundError(f"Run process_catchment first, missing:\n{projected_dem_path}")

        seismic_sta_path = Path(output_dir) / "seis_sta.shp"
        point2gpd(
            lon=self.seis_meta["seis_lon"].iloc[event_id],  # float, unit by degree
            lat=self.seis_meta["seis_lat"].iloc[event_id],  # float, unit by degree
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

        return png_path

    def calculate_statistic(self, event_id, num_d=None):

        output_dir = self.get_output_dir(event_id)
        projected_dem_path = self.get_projected_dem_path(event_id)

        if num_d is None:
            num_d = self.num_d

        if projected_dem_path.exists() is False:
            raise FileNotFoundError(f"Run process_catchment first, missing:\n{projected_dem_path}")

        seis_sta_name = (
            f"{self.seis_meta['seis_network'].iloc[event_id]}-"
            f"{self.seis_meta['seis_station'].iloc[event_id]}-"
            f"{self.seis_meta['seis_channel'].iloc[event_id]}"
        )
        seis_lon = self.seis_meta["seis_lon"].iloc[event_id]
        seis_lat = self.seis_meta["seis_lat"].iloc[event_id]

        # (1) calculate the hydrogeomorphic features
        geometry, relief, station_metrics = calculate_catchment(
            projected_dem_path=projected_dem_path,
            catchment_path=output_dir / "catchment.shp",
            main_df_channel_path=output_dir / "main_df_channel.shp",
            main_df_channel_extend_path=output_dir / f"main_df_channel_extend_{self.channel_extend}m.shp",
            stations=[(seis_sta_name, seis_lon, seis_lat)],  # List[tuple]
            n=num_d,
        )

        # (2) one-row table
        geo_row = pd.Series(geometry).round(4).to_frame().T
        relief_row = pd.Series(relief).round(4).to_frame().T
        sta_row = station_metrics.reset_index(drop=True)
        df = pd.concat([geo_row, relief_row, sta_row], axis=1)

        df["seis_cat"] = self.seis_meta["seis_cat"].iloc[event_id]
        df["metadata_row"] = event_id
        df["identifier"] = seis_sta_name
        df["dem_outlet_lat"] = self.dem_meta["dem_outlet_lat"].iloc[event_id]
        df["dem_outlet_lon"] = self.dem_meta["dem_outlet_lon"].iloc[event_id]

        return df
