#!/bin/bash -l
#SBATCH --job-name=wd
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=wd.%j.out
#SBATCH --error=wd.%j.err

module purge
module load Python/3.11.3-GCCcore-12.3.0
module load SciPy-bundle/2023.07-gfbf-2023a        # numpy 1.25, pandas 2.0.3, xarray 2023.6
python - <<'PY'
import pandas, xarray, netCDF4, numpy
print("✓ pandas", pandas.__version__)
print("✓ xarray", xarray.__version__)
PY



#module purge                      # optional, keeps env clean
# Load ONLY a plain Python if your cluster needs a module to get python itself.
#module load Python/3.11.3-GCCcore-12.3.0   # or comment out if not needed

# Activate your venv
source "$VSC_SCRATCH/venv_merge/bin/activate"

# (optional sanity check)
python - <<'PY'
import xarray, netCDF4, sys
print("Python:", sys.version.split()[0])
print("xarray:", xarray.__version__)
print("netCDF4:", netCDF4.__version__)
PY

# Run your driver script (not the module with self-tests)
python /rhea/scratch/brussel/111/vsc11128/withdrawals/water_withdrawal_yearly.py

deactivate

