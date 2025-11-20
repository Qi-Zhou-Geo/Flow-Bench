#!/bin/bash
#SBATCH -t 01:00:00              # time limit: (D-HH:MM:SS)
#SBATCH --job-name=prepare_data  # job name, "Qi_run"

#SBATCH --ntasks=1                 # each individual task in the job array will have a single task associated with it
#SBATCH --array=1-148              # job array id
#SBATCH --mem-per-cpu=8G		       # Memory Request (per CPU; can use on GLIC)

#SBATCH --output=logs/out_%A_%a_%x.txt  # Standard Output Log File
#SBATCH --error=logs/err_%A_%a_%x.txt   # Standard Error Log File

mkdir -p "logs"
project_path="/storage/vast-gfz-hpc-01/home/qizhou/3paper/Flow_Bench"

source /home/qizhou/miniforge3/bin/activate
conda activate seismic

# Define the parameter array
parameter1=($(seq 1 148)) # 1 to num_of_jobs
parameter1_idx=$((SLURM_ARRAY_TASK_ID - 1))

# Get the current parameter value
current_parameter1="${parameter1[$parameter1_idx]}"


# Print for debugging
echo "Running event index: $current_parameter1"
# Run the Python script with the --id argument
srun python "${project_path}/pipeline/cache_events/get_all_events.py" --id "$current_parameter1"


# delete the empty logout file
OUT_FILE="logs/out_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_NAME}.txt"
ERR_FILE="logs/err_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_NAME}.txt"

[ -e "$OUT_FILE" ] && [ ! -s "$OUT_FILE" ] && rm "$OUT_FILE"
[ -e "$ERR_FILE" ] && [ ! -s "$ERR_FILE" ] && rm "$ERR_FILE"