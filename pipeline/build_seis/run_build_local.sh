# Last modified: 2026-11-10T15:17:36
# Author: Qi Zhou

#!/bin/bash

project_path="/Users/qizhou/#python/Flow-Bench-geo"

# activate the env
source /usr/local/Caskroom/mambaforge/base/etc/profile.d/conda.sh
source /usr/local/Caskroom/mambaforge/base/etc/profile.d/mamba.sh
mamba activate flowBench

mkdir -p "${project_path}/cache/build_seis_logs"

# Run 5 tasks in parallel
max_jobs=5
count=0

for idx in $(seq 0 163) # sh index from 0 and will include the 163
do
    echo "Starting event index: $idx"

    log_file="${project_path}/cache/build_seis_logs/event_${idx}.log"
    python "${project_path}/pipeline/build_seis/run_build.py" --event_id "$idx" > "$log_file" 2>&1 &

    count=$((count + 1))

    if [ "$count" -ge "$max_jobs" ]
    then
        wait
        count=0
    fi
done

wait
echo "All jobs completed."