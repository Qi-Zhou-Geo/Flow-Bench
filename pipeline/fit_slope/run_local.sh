#!/bin/bash

project_path="/Users/qizhou/#python/Flow-Bench"


# Load conda into this shell
# find the local conda -> conda info | grep 'base environment'
source /usr/local/Caskroom/mambaforge/base/etc/profile.d/conda.sh
source /usr/local/Caskroom/mambaforge/base/etc/profile.d/mamba.sh
mamba activate flow-bench

for idx in $(seq 1 148)
do
    echo "Running event index: $idx"
    python "${project_path}/pipeline/fit_slope/main.py" --id "$idx"
done
