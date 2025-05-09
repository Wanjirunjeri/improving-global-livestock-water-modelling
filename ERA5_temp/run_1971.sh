#!/usr/bin/env bash
#SBATCH --job-name=era5_1971
#SBATCH --output=era5_1971-%j.out
#SBATCH --time=14:00:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1

module purge
module load Python/3.11.3-GCCcore-12.3.0   # same interpreter you just tested

echo "Running on $(hostname) with $(python -V)"
python download_1971.py

