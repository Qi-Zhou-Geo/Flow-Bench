## 📢 Welcome to **Flow-Bench**:
A global seismic record of channelized flow events.
---

### What Flow-Bench Offers

Flow-Bench provides a **global seismic record of channelized flow events**, 
offering an open-access, well-labeled seismic dataset with accompanying data quality and uncertainty information.  

Flow-Bench (v0.3) comprises **139 events**:
- **66 debris flows** from Illgraben (2013–2014, 2019–2020, and 2022)  
- **73 debris flows** from locations outside Illgraben  
- **1 glacial lake outburst flood (GLOF)**  
- **1 lahar**

These events originate from **21 catchments** and represent **runoff-generated debris flows** 
occurring across diverse environmental settings:
- Post-fire catchments (e.g., Museum Fire and Montecito)  
- Post-earthquake catchments (e.g., Ramche, Foutangba, and Ergou)  
- High-erosion catchments (e.g., Chalk Cliffs and Illgraben)

For more details and visualizations, 
visit the [Flow-Bench project page](https://qi-zhou-geo.github.io/Flow-Bench/).


### 🛠️ 0. Major Changes in v0.3

(1) **Flow-Bench Model**  
   - Built the Flow-Bench model to process seismic traces.  
   - Defines the event start and end times using the STA/LTA method.  
   - Calculates the spectral exponent $\beta$ in  $PSD(f) \propto f^{\beta}$
   - Identifies the most similar debris flows using DWT distance methods, referencing Illgraben events.  

(2) **Metadata and Data Access**  
   - Opens the [metadata](data/event_catalog/Flow_Bench_Catalog_work_v0dot3.txt) and provides a data [downloader](download_raw_data.py) for easy access to the seismic records.

This version is backed up at [zenodo](https://doi.org/10.5281/zenodo.17432440).<br>

### 🚀 1. How to Use Our Pre-trained Models on Your Data?
Check the [tutorial](demo/tutorial.ipynb) and run it on 
[![Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Qi-Zhou-Geo/Flow-Bench/blob/main/demo/tutorial.ipynb)

### ❓️2. Have Questions? <br>
1.1 Start by reading our related paper <br>
**Qi Zhou**, Hui Tang, Michael Dietze, Fabian Walter, Dongri Song, Yan Yan, Shuai Li, and Jens M. Turowski. <br>
"Similarity of Debris Flows in Seismic Records." <br>
**_Preprint_** (submitted to AGU Advance at August 2025). <br>
[Click here for the manuscript](https://doi.org/10.22541/essoar.175676964.46168374/v1) <br>

If you still have questions, feel free to contact us.

### 💪 3. Contributors <br>
**[Qi Zhou](https://github.com/Qi-Zhou-Geo)** <br>
qi.zhou@gfz.de or qi.zhou.geo@gmail.com <br>

**[Kshitij Kar](https://github.com/Kshitij301199)** <br>
kshitij.kar@gfz-potsdam.de <br>
