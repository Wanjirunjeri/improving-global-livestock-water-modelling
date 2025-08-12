#!/bin/bash
#SBATCH --job-name=livestock_wd_yearly
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=log_%j.out


module purge
module load  Python/3.11.3-GCCcore-12.3.0 
module load  SciPy-bundle/2023.07-gfbf-2023a
module load  matplotlib/3.7.2-gfbf-2023a
module load netcdf4-python/1.6.4-foss-2023a
#module load netCDF/4.9.2-gompi-2023a
module load dask/2023.9.2-foss-2023a
module load xarray/2023.9.0-gfbf-2023a
module load h5netcdf/1.2.0-foss-2023a



#python water_withdrawal.py
srun python -u water_withdrawal_yearly.py
#           

