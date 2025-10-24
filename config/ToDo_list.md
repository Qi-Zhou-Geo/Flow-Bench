## Preparation for running "Flow-Bench"

### 0. Check/Install Git and Conda
Open terminal and check your git version. <br>
If not installed, refer to: <br>
- Git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git <br>
- Conda: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html <br>
```sh
git --version 
conda --version
```

### 1. Clone "Flow-Bench" from GitHub
```sh
git clone https://github.com/Qi-Zhou-Geo/Flow-Bench.git
cd Flow-Bench
```

### 2. Create Conda Environment
```sh
# QZ export his conda env from Glic by:
# conda env export > Flow-Bnech-env.yml
# then QZ manually ask ChatGPT to remove the Linux required packages

# Create environment from config file
conda env create -f config/Flow-Bnech-env.yml

```

### 3. Verify Installation
```sh
conda activate flow-bench
conda info --envs
```

### 4. Download the raw seismic data
Make sure you have enough space to save the raw data. 
```sh
python functions/downloader/download_raw_data.py
```

If you want to save the data elsewhere, please pass the path.
```sh
python functions/downloader/download_raw_data.py --output_folder "/path/to/your/data"
```
