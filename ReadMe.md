```sh
# Last modified: 2026-11-23T21:39:32
# Author: Qi Zhou
```

## 📢 Welcome to **Flow-Bench**

**Flow-Bench** is a global seismic and hydrogeomorphic dataset of debris flows.

---

### ⁉️ Why do we need Flow-Bench?
Debris flows are fast, destructive mass movements that pose hazards in mountain regions. Seismic monitoring is non-invasive and provides observations at high temporal resolution, but seismic records and catchment information are rarely compiled across sites. Currently, we still lack a standardized dataset to support us for (1) cross-catchment analyses, (2) event-detector evaluation, and (3) early-warning system design.

### 🪜 What is in Flow-Bench?

- **164 seismic records** of individual debris flows (includes one GLOF, one lahar, and one flood) from **31 catchments** worldwide.
- **Hydrogeomorphic attributes** for each catchment.
- An open, standardized format shared across all regions.

### 🍻 What can you do with it?

**Link catchments to flow behavior**
- Investigate relationships between static catchment characteristics and dynamic debris-flow properties inferred from seismic data

**Benchmark detection models**
- Train and evaluate seismic-based debris-flow detection models across sites

**Calibrate physical models**
- Use the records to constrain physically based debris-flow models

Together, these support cross-catchment analyses and more generalizable monitoring and early-warning methods.

You can find the [demo](demo/how_to_play.md) here.

### 🛠️ Major changes for v0.5

See [docs/v0dot5.md](docs/v0dot5.md) for details.

### 📚 Reference

If you find this dataset useful, please cite our paper.

```bibtex
@inproceedings{zhou2025similarity,
  title={Similarity and Diversity of Debris Flow Footprints in Seismic Records},
  author={Zhou, Qi and Tang, Hui and Dietze, Michael and Walter, Fabian and Song, Dongri and Yan, Yan and Li, Shuai and Turowski, Jens},
  booktitle={EGU General Assembly Conference Abstracts},
  pages={EGU25--12267},
  year={2025}
}
```