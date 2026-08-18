#!/bin/bash
#SBATCH -t 03:00:00                # time limit: (D-HH:MM:SS)
#SBATCH --job-name=archive         # job name, "Qi_run"

#SBATCH --ntasks=1                 # each individual task in the job array will have a single task associated with it
#SBATCH --array=1-1                # job array id, 1 to N

#SBATCH --mem-per-cpu=16G		   # Memory Request (per CPU; can use on GLIC)

#SBATCH --output=out_%A_%a_%x.txt  # Standard Output Log File
#SBATCH --error=err_%A_%a_%x.txt   # Standard Error Log File


source /home/qizhou/miniforge3/bin/activate
conda activate flow-bench

srun python s01_download_from_glic.py
