#!/bin/bash

pip install --user --upgrage cdsapi


module purge
module load Python/3.11.3-GCCcore-12.3.0

python - <<'PY'
import sys, importlib.metadata as m
try:
    v = m.version("cdsapi")          # works even when cdsapi lacks __version__
    print("✓ cdsapi", v, "is installed and importable")
except m.PackageNotFoundError:
    print("✗ cdsapi not found on this Python")
PY

