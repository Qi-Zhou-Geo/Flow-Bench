#!/bin/bash

project_path="/Users/qizhou/#python/#GitHub_saved/Flow-Bench"


# Load conda into this shell
# find the local conda -> conda info | grep 'base environment'
source /Users/qizhou/opt/anaconda3/etc/profile.d/conda.sh
conda activate flow-alert

for idx in $(seq 1 133)
do
    echo "Running event index: $idx"
    python "${project_path}/pipeline/fit_slope/main.py" --id "$idx"
done
