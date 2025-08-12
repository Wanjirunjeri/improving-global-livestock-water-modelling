#!/bin/bash
#SBATCH --job-name=plot_livestock
#SBATCH --output=logs/plot_livestock_%j.out


module load Python/3.11.3-GCCcore-12.3.0
source $VSC_SCRATCH/venv_merge/bin/activate
#python monthly_totals.py
python pixel_monthly_totals.sh

