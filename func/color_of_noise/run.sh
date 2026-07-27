#!/bin/bash
#SBATCH -t 4-00:00:00              # time limit: (D-HH:MM:SS) 
#SBATCH --job-name=synth           # job name, "Qi_run"

#SBATCH --ntasks=1                 # each individual task in the job array will have a single task associated with it
#SBATCH --mem-per-cpu=8G          # Memory Request (per CPU; can use on GLIC)

#SBATCH --chdir=/storage/vast-gfz-hpc-01/home/qizhou/3paper/3Diversity-of-Debris-Flow-Footprints/functions/color_of_noise # set working dir
#SBATCH --output=out_%A_%a_%x.txt  # Standard Output Log File
#SBATCH --error=err_%A_%a_%x.txt   # Standard Error Log File

# Activate the Python environment
source /home/qizhou/miniforge3/bin/activate
conda activate seismic

# Define the parameter arrays
parameter1=("white_noise" "pink_noise" "red_noise")
parameter2=("0.001" "0.005" "0.01" "0.05" "0.1" "0.5" "1" "5" "10" "100")
##########=("157" "158" "159" "160" "161" "162")

srun python main_colored_noise.py --noise_type_list "${parameter1[@]}" --intensity_ratio_list "${parameter2[@]}"
