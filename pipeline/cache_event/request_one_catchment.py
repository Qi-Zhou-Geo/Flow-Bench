#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-02T15:14:29
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import pandas as pd
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

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
from func.download.seis_wrapper import one_seis_event

# unique identifier for the all events
fb = FlowBenchSeis(version="essd")
# load the meta
seis_meta = fb.get_metadata(meta_type="seis", print_meta=False)
event_meta = fb.get_metadata(meta_type="event", print_meta=False)
dem_meta = fb.get_metadata(meta_type="dem", print_meta=False)

f_min, f_max = 1, 25
event_id = 118
for idx, s in enumerate(["2021-07-29T00:00:00", "2021-07-30T00:00:00", "2021-07-31T00:00:00", "2021-08-01T00:00:00"]):
    starttime = UTCDateTime(s)
    endtime = UTCDateTime(s) + 3600 * 24

    st_raw, _ = one_seis_event(seis_meta, event_meta, event_id, starttime, endtime, f_min, f_max)

    # region
    # catchment meta
    seis_meta_copy = seis_meta.copy()
    continent = seis_meta_copy["continent"][event_id]
    seis_cat = seis_meta_copy["seis_cat"][event_id]

    # seismic meta
    seis_client = seis_meta_copy["seis_client"][event_id]
    seis_network = seis_meta_copy["seis_network"][event_id]
    seis_station = str(seis_meta_copy["seis_station"][event_id])
    seis_location = seis_meta_copy["seis_location"][event_id]
    if pd.isna(seis_location) is True:
        seis_location = ""
    seis_channel = seis_meta_copy["seis_channel"][event_id]
    seis_response = seis_meta_copy["seis_response"][event_id]
    sensor_type = seis_meta_copy["seis_sensor"][event_id]
    year = UTCDateTime(starttime).year
    julday = UTCDateTime(starttime).julday
    # endregion

    local_dir = "data/seis_raw"
    sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}"
    file_name = f"{seis_network}.{seis_station}.{seis_channel}.{year}.{julday:03d}.mseed"
    st_raw_path = Path(project_root) / local_dir / sub_folder / file_name
    st_raw_path.parent.mkdir(parents=True, exist_ok=True)

    assert st_raw is not None
    st_raw.write(st_raw_path, format="MSEED")

    if idx == 0:
        client = Client(seis_client)
        inv_or_paz = client.get_stations(
            network=seis_network,
            station=seis_station,
            location=seis_location,
            channel=seis_channel,
            level="response",
            format="xml",
        )

        sub_folder = f"{continent}/{seis_cat}/{year}/{seis_station}"
        file_name = "inventory.xml"
        inv_path = Path(project_root) / local_dir / sub_folder / file_name

        assert inv_or_paz is not None
        inv_or_paz.write(inv_path, format="STATIONXML")
