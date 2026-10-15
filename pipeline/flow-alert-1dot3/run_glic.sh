#!/bin/bash
#SBATCH -t 00:30:00                # time limit: (D-HH:MM:SS)
#SBATCH --job-name=test            # job name, "Qi_run"

#SBATCH --ntasks=1                  # each individual task in the job array will have single task associated with it
#SBATCH --array=59-140                # job array id 59-140

#SBATCH --mem-per-cpu=64G            # Memory Request (per CPU; can use on GLIC)

#SBATCH --begin=2023-10-20T09:00:00  # job start time, if it later than NOW, job will be run immediatly.

#SBATCH --output=logs/out_%A_%a_%x.txt  # Standard Output Log File
#SBATCH --error=logs/err_%A_%a_%x.txt   # Standard Error Log File

# create the “log” folder in case it doesn't exist
mkdir -p "logs"


# GFZ Configuration with GPUs
module use /cluster/spack/2022b/share/spack/modules/linux-almalinux8-icelake
# load environment
source /home/qizhou/miniforge3/bin/activate
conda activate FlowAlert


start_time=$(date)
echo "Job started at: $start_time"


# Run your Python script using srun with the parameters
event_id="$SLURM_ARRAY_TASK_ID"
srun python test_all_events.py --event_id "$event_id"

end_time=$(date)
echo "Job finished at: $end_time"
echo "Total running time: $(( $(date -d "$end_time" +%s) - $(date -d "$start_time" +%s) )) seconds"
