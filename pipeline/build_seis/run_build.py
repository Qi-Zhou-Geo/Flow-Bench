#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-23T18:00:17
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import argparse

import math
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

# import custom func.
from func.flow_bench.FlowBench import FlowBenchSeis
from func.flow_bench.unique_identifier import build_identifier

from func.seismic.welch_spectrum import welch_psd
from func.seis_feature.calculate_feature import seis_ES
from func.seismic.chunk_st2seq import chunk_data
from func.seismic.denoising import denoise_st


def try_request_event(fb, event_id, f_min, f_max, starttime, endtime, buffer_hour):

    try:
        st_raw, st_cooked = fb.request_one_seis_event(
            event_id=event_id,
            f_min=f_min,
            f_max=f_max,
            starttime=starttime,
            endtime=endtime,
            buffer_hour=buffer_hour,
        )
    except Exception:  # noqa: BLE001
        buffer_hour = 0

        try:
            st_raw, st_cooked = fb.request_one_seis_event(
                event_id=event_id,
                f_min=f_min,
                f_max=f_max,
                starttime=starttime,
                endtime=endtime,
                buffer_hour=buffer_hour,
            )
            msg = f"Do not enough data was available for {event_id, f_min, f_max, starttime, endtime}.\nbuffer_hour={buffer_hour}\n\n"
            print(msg)
        except Exception as exc:
            # from exc preserves the underlying error for debugging
            msg = "Error! fb.request_one_seis_event failed."
            raise ValueError(msg) from exc

    return st_raw, st_cooked


def main(event_id, sub_window_size, denoising_window_size, denoising_method, window_overlap, fmt):

    # unique identifier for the all events
    identifier = build_identifier(version=version, fmt="%Y-%m-%dT%H:%M:%S")
    fb = FlowBenchSeis(version=version)
    # load the meta
    seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
    event_meta = fb.get_metadata(meta_type="event", print_meta=False)
    dem_meta = fb.get_metadata(meta_type="dem", print_meta=False)

    sampling_rate = seis_meta["seis_sampling_rate"][event_id]
    starttime = event_meta["event_time_s"][event_id]
    endtime = event_meta["event_time_e"][event_id]

    # region >> sub-window level
    ## set freq bin
    if sampling_rate >= 50:
        f_lower_bin = [1, 5, 10, 15, 20]  # Hz
        f_upper_bin = [5, 10, 15, 20, 24.9]  # Hz
        f_max = 25  # Hz
    else:
        f_lower_bin = [1, 2, 4, 6, 8]  # Hz
        f_upper_bin = [2, 4, 6, 8, 9.9]  # Hz
        f_max = 10  # Hz

    # buffer 3 hours before and after the debris-flow event
    duration = UTCDateTime(endtime) - UTCDateTime(starttime)
    buffer_hour = math.ceil(duration / 3600) * 3  # type: ignore
    st_raw, st_cooked = try_request_event(
        fb=fb,
        event_id=event_id,
        f_min=1,
        f_max=f_max,
        starttime=starttime,
        endtime=endtime,
        buffer_hour=buffer_hour,
    )

    stats = st_cooked[0].stats  # type: ignore
    assert sampling_rate == int(stats.sampling_rate), f"SPS is not equal stats.sampling_rate={stats.sampling_rate}."
    data_m_s = st_cooked[0].data

    ## chunk the data
    t_float, t_str, chunk_x = chunk_data(
        data=data_m_s,
        data_start_time=stats.starttime.strftime(fmt),
        data_sps=sampling_rate,
        window_size=sub_window_size,
        window_overlap=window_overlap,
        fmt=fmt,
    )

    ## loop ES
    num_bin = len(f_lower_bin)
    seismic_energy = np.empty(shape=(len(chunk_x), num_bin), dtype=float)
    for sub_idx, data_in_subwindow in enumerate(chunk_x):
        ES = seis_ES(
            data_m_s=data_in_subwindow,
            nyquist_f=sampling_rate / 2,
            num_bin=num_bin,
            f_lower_bin=f_lower_bin,
            f_upper_bin=f_upper_bin,
        )
        seismic_energy[sub_idx] = ES

    ## prepare output
    t1 = np.array(t_str).reshape(-1, 1)
    t2 = np.array(t_float).reshape(-1, 1)
    seismic_energy = np.concatenate((t1, t2, seismic_energy), axis=1)  # by column
    # endregion

    # region >> event level
    ## update the buffer
    buffer_hour = 0

    # buffer 0 hours before and after the debris-flow event
    st_raw, st_cooked = try_request_event(
        fb=fb,
        event_id=event_id,
        f_min=1,
        f_max=sampling_rate / 2,
        starttime=starttime,
        endtime=endtime,
        buffer_hour=buffer_hour,
    )

    # this apply to 1 to nyquist_f Hz
    data_m_s = st_cooked[0].data
    freq, psd, psd_unit = welch_psd(
        data=data_m_s,
        sampling_rate=sampling_rate,
        f_min=1,
        f_max=sampling_rate / 2,
        segment_window=10,
        scaling="density",
        unit_dB=True,
    )
    feat_f_dom = freq[np.argmax(psd)]
    feat_f_dom_psd = np.max(psd)

    ## amplitude domain
    low_sampling_rate, denoised_st = denoise_st(
        st=st_cooked.copy(),
        window_size=denoising_window_size,
        window_overlap=window_overlap,
        denoising_method=denoising_method,
        fmt=fmt,
    )
    denoised_data_m_s = denoised_st[0].data  # type: ignore

    feat_max_amp = np.max(denoised_data_m_s)
    feat_max_amp_t = UTCDateTime(denoised_st[0].stats.starttime) + np.argmax(denoised_data_m_s) / low_sampling_rate  # type: ignore
    feat_max_amp_t = feat_max_amp_t.strftime(fmt)

    feat_q75_amp = np.quantile(a=denoised_data_m_s, q=0.75)
    feat_q25_amp = np.quantile(a=denoised_data_m_s, q=0.25)
    # endregion

    # region >> save results
    npz_path = Path(project_root) / f"data/seis_cooked/{identifier[event_id]}.npz"
    npz_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        ##
        # overall meta
        "event_id": event_id,
        "identifier": str(identifier[event_id]),
        "version": str(version),
        "author": "QZ",
        "create_time": UTCDateTime.now().strftime(fmt),
        ##
        # seismic meta
        "station": stats.station,
        "channel": stats.channel,
        "sampling_rate[Hz]": stats.sampling_rate,
        "event_start_time[UTC+0]": event_meta["event_time_s"][event_id],
        "event_end_time[UTC+0]": event_meta["event_time_e"][event_id],
        "buffer_time[hour]": math.ceil(duration / 3600) * 3,  # type: ignore
        "min_distance_to_df_channel[km]": dem_meta["geo_d"][event_id],
        ##
        # psd
        "psd[dB]": psd,
        "frequency[Hz]": freq,
        ##
        # sub-window level
        "f_lower_bin": np.asarray(f_lower_bin),
        "f_upper_bin": np.asarray(f_upper_bin),
        "seismic_energy[dimensionless]": seismic_energy,
        ##
        # event level
        "feat_f_dom": feat_f_dom,
        "feat_f_dom_psd": feat_f_dom_psd,
        "feat_max_amp": feat_max_amp,
        "feat_max_amp_t": feat_max_amp_t,
        "feat_q75_amp": feat_q75_amp,
        "feat_q25_amp": feat_q25_amp,
    }
    np.savez_compressed(file=npz_path, **output)
    # endregion

    # region save to match the paper Table A4
    npz_path = Path(project_root) / f"data/seis_cooked/{identifier[event_id]}_feat.npz"
    npz_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        ##
        # overall meta
        "event_id": event_id,
        "identifier": str(identifier[event_id]),
        "version": str(version),
        "author": "QZ",
        "create_time": UTCDateTime.now().strftime(fmt),
        ##
        "event_type": str(identifier[event_id]),  # this is saved in xlsx format
        "event_t_s": event_meta["event_time_s"][event_id],  # UTC+0
        "event_t_e": event_meta["event_time_e"][event_id],  # UTC+0
        ##
        "event_pub_doi": str(identifier[event_id]),  # this is saved in xlsx format
        ##
        "feat_max_amp": feat_max_amp,  # m/s
        "feat_max_amp_t": feat_max_amp_t,  # UTC+0
        "feat_f_dom": feat_f_dom,  # Hz
        "feat_f_dom_psd": feat_f_dom_psd,  # dB
        ##
        "f_lower_bin": np.asarray(f_lower_bin),  # Hz
        "f_upper_bin": np.asarray(f_upper_bin),  # Hz
        "seismic_energy[dimensionless]": seismic_energy,  # as 2D array
    }
    np.savez_compressed(file=npz_path, **output)
    # endregion


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event_id", type=int)
    args = parser.parse_args()

    # region >> input params
    version = "essd"
    fmt = "%Y-%m-%dT%H:%M:%S"
    sub_window_size = 60  # second
    denoising_window_size = 10  # second
    denoising_method = "RMS"
    window_overlap = 0  # no unit
    # endregion

    main(args.event_id, sub_window_size, denoising_window_size, denoising_method, window_overlap, fmt)
