#!/bin/bash
#SBATCH -t 12:00:00                # time limit: (D-HH:MM:SS)
#SBATCH --job-name=test            # job name, "Qi_run"

#SBATCH --ntasks=1                  # each individual task in the job array will have single task associated with it
#SBATCH --array=1-6                # job array id 59-140

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

station_list=("NEP08" "NEP07" "NEP06" "NEP10" "NEP05" "NEP04")
seis_station="${station_list[$((SLURM_ARRAY_TASK_ID - 1))]}"

# Run your Python script using srun with the parameters
echo "Array task: $SLURM_ARRAY_TASK_ID; Station: $seis_station"
srun python test_by_catchment.py --seis_station "$seis_station"

end_time=$(date)
echo "Job finished at: $end_time"
echo "Total running time: $(( $(date -d "$end_time" +%s) - $(date -d "$start_time" +%s) )) seconds"
