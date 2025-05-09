#!/bin/bash

module load python/3.11         # load the Python you plan to use
pip install --user cdsapi
python -c "import cdsapi, sys; print('✓ cdsapi in', sys.executable)"

