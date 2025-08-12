#!/bin/bash
#SBATCH --job-name=plot_livestock
#SBATCH --mem=16G
#SBATCH --output=potlivestock.out


module load Python/3.11.3-GCCcore-12.3.0
source $VSC_SCRATCH/venv_merge/bin/activate

#pip install --upgrade "shapely>=2.0" "pyogrio>=0.7.2" "geopandas>=0.13"


#pip install regionmask
#python monthly_totals.py

#python pixel_monthly_totals.sh
#python spotter.py

#python glob_plot.py

python mylivds_glob.py

#python annual_lww_plot.py
#python perc_diff.py
#python per_pixel_monthly_totals2.py

#python comparison.py
