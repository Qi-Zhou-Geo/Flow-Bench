```sh
# Last modified: 2026-11-10T17:22:16
# Author: Qi Zhou
```
## Data and code used for Flow-Bench v0.5

### Data
**(0) Seismic metadata**

The Excel catalog is included in *`Flow-bench_v0dot5.zip`*. It contains the information needed to download raw seismic data from FDSN services or from the cited archives when data are unavailable through FDSN. The file is located at [~/Flow-bench_v0dot5/data/event_catalog/Flow_Bench_Catalog_essd.xlsx](../data/event_catalog/Flow_Bench_Catalog_essd.xlsx).

**(1) Unpublished seismic data**

These records are included in *`seis_raw_v0dot5.zip`* and cover Ergou, Foutangba, Huangbengliu, Hongqi, Illgraben (2021-2023), Reshuigou, Wandong, and Yanzigou.

**(2) Archived seismic data**

Data that are unavailable through FDSN services are included in *`seis_raw_v0dot5.zip`*. We acknowledge the original sources and retain their original licenses:

- Goulinping (Yang et al., 2024): [DOI](https://doi.org/10.5281/zenodo.10773103) (Creative Commons Attribution 4.0 International, CC BY 4.0)
- Hailuogou (Pang et al., 2026): [DOI](https://doi.org/10.5281/zenodo.19166000) (CC BY 4.0)
- Jiangjia (Wei et al., 2025): 2023–2024 data at [DOI](https://doi.org/10.12072/ncdc.ddfors.db6804.2025) and 2025 data at [DOI](https://doi.org/10.12072/ncdc.ddfors.db7459.2026) (both CC BY 4.0)
- Tianmo (Song et al., 2025): [DOI](https://doi.org/10.5281/zenodo.15125198) (CC BY 4.0)
- The Ruapehu seismic data (Walsh et al., 2023; [DOI](https://doi.org/10.5194/nhess-23-1029-2023) were last accessed at [DOI](https://theghub.org/resources/4890) on 14 November 2024. The original link is no longer available; a copy is included in this archive *`seis_raw_v0dot5.zip`*.


**(3) Sensor responses**

Sensor response *`XML`* files are included with the seismic data in *`seis_raw_v0dot5.zip`*. If the *`XML`* unavailable, the file [~/Flow-bench_v0dot5/config/paz_meta.py](../config/paz_meta.py) contains the poles and zeros used for instrument-response removal.

**(4) Processed seismic and hydrogeomorphic data**

Processed seismic and hydrogeomorphic characteristics for all events and catchments are provided in [~/Flow-bench_v0dot5/data/seis_cooked](../data/seis_cooked) and [~/Flow-bench_v0dot5/data/hydro_cooked](../data/hydro_cooked), respectively. To regenerate these results,[~/Flow-bench_v0dot5/run pipeline/build_seis/run_build.py](../pipeline/build_seis/run_build.py) and [~/Flow-bench_v0dot5/pipeline/build_geo/run_all.py](../pipeline/build_geo/run_all.py) on your computer.

### Code
The code used for Flow-Bench (v0.5) is available at [Flow-Bench](https://github.com/Qi-Zhou-Geo/Flow-Bench).

### Usage
To use the code, place the raw seismic data in [~/Flow-bench_v0dot5/data/seis_raw](../data/seis_raw). If you download data from FDSN using the code [demo](../demo/how_to_play.md), the raw records and seismic *`XML`* files will be saved at [~/Flow-bench_v0dot5/data/seis_raw](../data/seis_raw).