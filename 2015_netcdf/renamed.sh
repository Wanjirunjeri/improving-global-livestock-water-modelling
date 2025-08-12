#!/usr/bin/env bash
set -euo pipefail

INDIR="/scratch/brussel/111/vsc11128/fao_validation/2015_netcdf"
OUTDIR="$INDIR"

# Make sure bash treats globs with no matches as empty (avoids literal *Da.tif)
shopt -s nullglob

# Associative map: code -> species
declare -A animal_map=(
  [Bf]=buffalo
  [Ch]=chicken
  [Ct]=cattle
  [Dk]=duck
  [Gt]=goat
  [Ho]=horse
  [Pg]=pig
  [Sh]=sheep
)

command -v gdal_translate >/dev/null 2>&1 || { echo "ERROR: gdal_translate not found in PATH"; exit 1; }

for file in "$INDIR"/*Da.tif; do
  base="$(basename "$file" .tif)"           # e.g., 5_Bf_2015_Da
  # Extract the 2nd underscore-separated token (Bf, Ch, ...)
  animal_code="${base#*_}"                  # drop up to first _
  animal_code="${animal_code%%_*}"          # keep up to next _
  animal_name="${animal_map[$animal_code]:-}"

  if [[ -z "$animal_name" ]]; then
    echo "WARN: No mapping for code '$animal_code' in '$base' — skipping."
    continue
  fi

  out="$OUTDIR/${animal_name}_2015.nc"
  echo "→ $base  ->  $(basename "$out")"
  gdal_translate -of netCDF "$file" "$out"
done

