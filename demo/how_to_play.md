```sh
# Last modified: 2026-11-03T14:54:00
# Author: Qi Zhou
```

# You can use `Flow-Bench` for different purposes.<br>Below are my recommended workflows.


## 📝 Seismic part
### 1. Download the debris-flow events

#### 1.1 Whole dataset
Use [s02_download_from_fdsn.py](../pipeline/download_seis/s02_download_from_fdsn.py) to download all the seismic data available through FDSN:

```python
# Download debris-flow seismic data hosted on FDSN.
fb.down_all_seis_data(buffer_day=buffer_day, data_source="FDSN")
```

Some records are not on FDSN (e.g., ncdc, Ghub, Zenodo, private). Use the `Nextcloud` option in the same script to get our pre-downloaded data:

```python
# Download our pre-downloaded data from Nextcloud.
# Original sources include ncdc, Ghub, Zenodo, and private datasets.
# For manual downloads, use the required format and folder structure.
# "format: ~/data/seis_raw/continent/catchment/year/station/channel/network.station.channel.year.day-of-year.mseed\n"
fb.down_all_seis_data(buffer_day=buffer_day, data_source="Nextcloud")
```

You can also download the [Zenodo archive](https://doi.org/10.5281/zenodo.23883084) yourself and put it in this structure:

`~/data/seis_raw/continent/catchment/year/station/channel/network.station.channel.year.day-of-year.mseed`

To get a longer noise period, you can increase `buffer_day`.
For other stations or components, you can update the seismic metadata [Flow_Bench_Catalog_essd.xlsx](../data/event_catalog/Flow_Bench_Catalog_essd.xlsx).
Or you can use the following function.


#### 1.2 One event
You can use `load_raw_fdsn` in [seis.py](../func/download/seis.py) to download a single event, or a station or channel that is not in [Flow_Bench_Catalog_essd.xlsx](../data/event_catalog/Flow_Bench_Catalog_essd.xlsx), for example:

```python
# please >> import load_raw_fdsn and cooking_recipe first
st_raw, inv_or_paz = load_raw_fdsn(
    # catchment meta
    continent="European",
    seis_cat="Illgraben",
    # seismic meta
    seis_client="GEOFON",
    seis_network="9J",
    seis_station="IGB02",
    seis_location="",
    seis_channel="HHZ",
    # response meta
    seis_response="xml",
    sensor_type="do-not-need",
    # event meta
    starttime="2014-07-12T12:00:00",
    endtime="2014-07-12T18:00:00",
    # default params
    save_st=False,
    save_inv=False,
    local_dir="data/seis_raw",
)
st_cooked = cooking_recipe(st=st_raw, inv_or_paz=inv_or_paz, f_min=1, f_max=25)
```

### 2. Retiming

You can use [timing.py](../pipeline/event_timing/timing.py) to update the debris-flow event start and end times. And you can change the default parameters, such as:

```python
f_min = 1  # Hz
f_max = 10  # Hz
thr_on = 0.3  # dimensionless
thr_off = 0.3  # dimensionless
sta = 180  # seconds
lta = 1800  # seconds
```

You should not trust a detected start time within the first and last `lta` window. For example, if the input window starts at `event_time_s_ref = "2014-07-12T12:00:00"` and `lta = 1800` seconds (30 minutes), you should only trust start times detected after `"2014-07-12T12:30:00"`.

If you want to change the reference time window, update `event_time_s_ref` and `event_time_e_ref` for the event in [Flow_Bench_Catalog_essd.xlsx](../data/event_catalog/Flow_Bench_Catalog_essd.xlsx). Please note that if you pass in a long data window (`event_time_e_ref - event_time_s_ref` is very big), you may see multiple detected start and end times.


### 3. Build the seismic features

You can use [run_build.py](../pipeline/build_seis/run_build.py) to build the seismic features. For example, the [seis_ES](../func/seis_feature/calculate_feature.py) function calculates the seismic energy in each frequency bin.

### 4. Check the data quality

To compare the debris-flow sismic records with the global high and low noise models, you can use `plot_Wolin2019_model` in [visualize_noise_model.py](../data/noise_model/visualize_noise_model.py). In theory, the signal of a debris-flow event should be above the global low-noise model.


## 📝 HydroGeo part

### 1. Get your personal key

Register a personal account at [OpenTopography](https://portal.opentopography.org/newUser) and save the key in `config/dem_key.yml` with the following content:

```yaml
Copernicus: "your-key-id" # replace `your-key-id` with your own key
```

### 2. Download the Copernicus 30 m DEM

You can use `download_dem` in [FlowBenchHydro](../func/flow_bench/FlowBench.py) to download the 30 m DEM for the events in the catalog.

If you want a larger or smaller DEM extent, update `dem_west_lon`, `dem_east_lon`, `dem_south_lat`, and `dem_north_lat` for the event in [Flow_Bench_Catalog_essd.xlsx](../data/event_catalog/Flow_Bench_Catalog_essd.xlsx).

Please note that an existing DEM will be reused to avoid unnecessary downloads. OpenTopography currently limits free Global Datasets API access to 200 requests per 24 hours for academic users and 50 requests per 24 hours for non-academic users. After changing the boundary, delete the corresponding DEM file in `data/hydro_raw/` so that the next run downloads a new one.


### 3. Build the hydrogeo features

For one event, use `FlowBenchHydro` in [FlowBench.py](../func/flow_bench/FlowBench.py), even if the event shares an outlet with other events. 

For the whole catalog, use [run_all.py](../pipeline/build_geo/run_all.py). Each unique catchment and outlet is processed only once, so if several events share them, only the first event's seismic station is used. The results are saved [here](../data/hydro_cooked/hydrogeomorphic_by_outlet.txt).


### 4. Change the WhiteboxTools parameters

We use the default WhiteboxTools (WBT) parameters defined in [wbt_params.py](../config/wbt_params.py), including `wbt_threshold` and `snap_dist`. You can change these settings in the file, just as you change the STA/LTA parameters for retiming.

After changing the parameters, rerun the processing, check the overview plot, and recalculate the hydrogeo features.

## 3. Check the outlet and DEM boundary

The `dem_outlet_lat` and `dem_outlet_lon` are manually defined for each event. If you have a better way to define the outlet, update them in [Flow_Bench_Catalog_essd.xlsx](../data/event_catalog/Flow_Bench_Catalog_essd.xlsx).

If the DEM is not big enough, update `dem_west_lon`, `dem_south_lat`, `dem_east_lon` and `dem_north_lat` of the event in [Flow_Bench_Catalog_essd.xlsx](../data/event_catalog/Flow_Bench_Catalog_essd.xlsx).

After editing the catalog, rerun the script to load the updated values.
