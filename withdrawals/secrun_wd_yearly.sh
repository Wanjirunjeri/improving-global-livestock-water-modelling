#!/usr/bin/env bash
#SBATCH --job-name=liv_wd_yearly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8       # grab every core on the node           # one thread per task
#SBATCH --mem=64G                     # take all ~1 TB RAM
#SBATCH --time=24:00:00
#SBATCH --output=log_%j.out

module purge
module load  Python/3.11.3-GCCcore-12.3.0
module load  SciPy-bundle/2023.07-gfbf-2023a
module load  netcdf4-python/1.6.4-foss-2023a
module load  xarray/2023.9.0-gfbf-2023a
module load  dask/2023.9.2-foss-2023a
module load  h5netcdf/1.2.0-foss-2023a

# Launch once per task (MPI) OR let dask-jobqueue start workers.
# For pure MPI-style fan‑out:
srun python -u water_withdrawal_yearly.py

