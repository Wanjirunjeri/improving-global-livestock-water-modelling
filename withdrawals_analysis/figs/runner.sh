#!/bin/bash
#SBATCH --job-name=liv_analysis
#SBATCH --mem=16G
#SBATCH --output=livestock.out


module load Python/3.11.3-GCCcore-12.3.0
source $VSC_SCRATCH/venv_merge/bin/activate
#pip install cartopy==0.21 regionmask geopandas 
pip install --force-reinstall "pandas<2.0"
python livestock_water_analysis.py

