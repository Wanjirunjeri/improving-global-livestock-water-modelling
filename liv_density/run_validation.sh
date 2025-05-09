#!/bin/bash
#SBATCH --job-name=validate_livestock
#SBATCH --output=validate_livestock.log
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --partition=skylake      # or zen4, ampere_gpu, etc.

module purge
module load Python/3.10.4-GCCcore-11.3.0            # module name may differ on your cluster
#module load  Python/3.10.4-GCCcore-11.3.0          # base Python for gfbf‑2023a
module load  SciPy-bundle/2022.05-foss-2022a    # numpy, pandas, scipy …
module load  xarray/2022.6.0-foss-2022a        # xarray extension
module load  matplotlib/3.5.2-foss-2022a      # matplotlib extension
module load  netcdf4-python/1.6.1-foss-2022a    # exact version may differ

# sanity‑check:
python - <<'PY'
import xarray, pandas, matplotlib
print('✓ xarray     ', xarray.__version__)
print('✓ pandas     ', pandas.__version__)
print('✓ matplotlib ', matplotlib.__version__)
print("netCDF4", netCDF4.__version__)
PY


python map_validation.py

