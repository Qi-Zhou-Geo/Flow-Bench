#!/bin/bash

project_path="/Users/qizhou/#python/Flow-Bench-geo"

# activate the env
source /usr/local/Caskroom/mambaforge/base/etc/profile.d/conda.sh
source /usr/local/Caskroom/mambaforge/base/etc/profile.d/mamba.sh
mamba activate flowBench

mkdir -p "${project_path}/data/cache/event_timing_logs"

# Run 8 tasks in parallel
max_jobs=8
count=0

for idx in $(seq 0 140) # $(seq 0 140)
do
    echo "Starting event index: $idx"

    log_file="${project_path}/data/cache/event_timing_logs/event_${idx}.log"
    python "${project_path}/pipeline/event_timing/timing.py" --event_id "$idx" > "$log_file" 2>&1 &

    count=$((count + 1))

    if [ "$count" -ge "$max_jobs" ]
    then
        wait
        count=0
    fi
done

wait
echo "All jobs completed."