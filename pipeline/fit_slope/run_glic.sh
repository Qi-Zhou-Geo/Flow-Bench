#!/bin/bash
#SBATCH -t 01:00:00              # time limit: (D-HH:MM:SS)
#SBATCH --job-name=fit_slope     # job name, "Qi_run"

#SBATCH --ntasks=1                 # each individual task in the job array will have a single task associated with it
#SBATCH --array=1-1                # job array id
#SBATCH --mem-per-cpu=8G		       # Memory Request (per CPU; can use on GLIC)

#SBATCH --output=logs/out_%A_%a_%x.txt  # Standard Output Log File
#SBATCH --error=logs/err_%A_%a_%x.txt   # Standard Error Log File

mkdir -p "logs"
project_path="/storage/vast-gfz-hpc-01/home/qizhou/3paper/Flow_Bench"

source /home/qizhou/miniforge3/bin/activate
conda activate seismic


for idx in $(seq 1 148)
do
    echo "Running event index: $idx"
    python "${project_path}/pipeline/fit_slope/main.py" --id "$idx"
done
