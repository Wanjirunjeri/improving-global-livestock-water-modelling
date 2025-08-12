#!/usr/bin/env bash
#SBATCH --job-name=livestock_wd_all
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=all.log

module purge
#module load Python/3.11.3-GCCcore-12.3.0    # xarray + netCDF4 stack
module load Python/3.10.4-GCCcore-11.3.0            # module name may differ on your cluster
module load  SciPy-bundle/2022.05-foss-2022a    # numpy, pandas, scipy …
module load  xarray/2022.6.0-foss-2022a        # xarray extension
module load  matplotlib/3.5.2-foss-2022a      # matplotlib extension
module load  netcdf4-python/1.6.1-foss-2022a 
module load  dask/2022.10.0-foss-2022a

python water.py


   

