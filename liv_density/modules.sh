#!/bin/bash

module purge                                   # clean env
module load  Python/3.10.4-GCCcore-11.3.0          # base Python for gfbf‑2023a
module load  SciPy-bundle/2022.05-foss-2022a    # numpy, pandas, scipy …
module load  xarray/2022.6.0-foss-2022a        # xarray extension
module load  matplotlib/3.5.2-foss-2022a      # matplotlib extension
# sanity‑check:
python - <<'PY'
import xarray, pandas, matplotlib
print('✓ xarray     ', xarray.__version__)
print('✓ pandas     ', pandas.__version__)
print('✓ matplotlib ', matplotlib.__version__)
PY
