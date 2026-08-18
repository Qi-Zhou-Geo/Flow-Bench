#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-18T16:55:53
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

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
# for metadata
from func.toolkit.xlsx_to_txt import xlsx2txt

# for download
from func.download.seis_wrapper import all_seis_data, one_seis_event

# for STA/LTA
from func.seismic.denoising import denoise_st
from func.sta_lta.forward_backward import forward_backward_sta_lta
from func.sta_lta.post_process import plot_sta_lta


class FlowBench:
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

        if meta_type == "all":
            column_s, column_e = 17, 19
        elif meta_type == "seis" or meta_type == "dem":
            column_s, column_e = 0, 12
        elif meta_type == "event":
            column_s, column_e = 17, 19
        else:
            raise ValueError(f"Unsupported meta_type: {meta_type}")

        df_meta = xlsx2txt(input_xlsx_path=meta_xlsx, output_txt_path=meta_txt, column_s=column_s, column_e=column_e)

        if print_meta is True:
            print(f"Flow-Bnech Metadata\nNum of rows: {len(df_meta.index)}\nName of columns: {df_meta.columns}\n\n")

        return df_meta

    def get_dem(self, seis_cat, dem_resolutio):

        # from seis_cat to the meta
        dem = 1  # download_dem(seis_cat, dem_resolutio)

        return dem

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
                f_min=self.f_min,
                f_max=self.f_max,
                # show and save
                show_plot=show_plot,
                save_plot=save_plot,
                png_path=png_path,
                png_name=png_name,
            )

        return sta_lta_timing


def usage(on_glic=False):

    fb = FlowBench(version="v2dot1dot2")

    # download the Non-FDSN data from Glic
    # there are may have E and N components data
    if on_glic is True:
        fb.down_all_seis_data(buffer_day=1, data_source="GLIC")

    # download all FSDN data
    fb.down_all_seis_data(buffer_day=1, data_source="FDSN")

    # # load the meta
    seis_met = fb.get_metadata(meta_type="seis", print_meta=False)
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)

    # request one evnet
    event_id = 160
    st_raw, st_cooked = fb.request_one_seis_event(event_id=90)
    st_raw.plot()  # type: ignore
    st_cooked.plot()
    sta_lta_timing = fb.get_event_t(st=st_cooked, show_plot=True, save_plot=True, event_id=event_id)
