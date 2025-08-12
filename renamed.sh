#!/usr/bin/env bash
# Rename Band1 to species names and merge per year (2010, 2015, 2020)
# You can run this from anywhere.
# Inputs are under:   $VSC_HOME/GLWD/liv_density/<YEAR>_netcdf
# Outputs will go to: $VSC_SCRATCH/fao_validation/<YEAR>_netcdf

set -euo pipefail

YEARS=(2010 2015 2020)
SPECIES=(buffalo cattle chicken duck goat horse pig sheep)

IN_BASE="$VSC_SCRATCH/fao_validation" #VSC_HOME/GLWD/liv_density"
OUT_BASE="$VSC_SCRATCH/fao_validation"

for yr in "${YEARS[@]}"; do
  INDIR="${IN_BASE}/${yr}_netcdf"
  OUTDIR="${OUT_BASE}/${yr}_out_netcdf"
  mkdir -p "${OUTDIR}"

  echo "============================"
  echo ">>> Year ${yr}"
  echo "Input dir : ${INDIR}"
  echo "Output dir: ${OUTDIR}"

  # 1) Rename variables (Band1 -> species)
  for sp in "${SPECIES[@]}"; do
    in="${INDIR}/${sp}_${yr}.nc"
    out="${INDIR}/${sp}_${yr}.ren.nc"
    if [[ ! -f "${in}" ]]; then
      echo "WARNING: Missing ${in}; skipping this species."
      continue
    fi
    echo "Renaming Band1 -> ${sp} in $(basename "${in}") …"
    cdo -O chname,Band1,${sp} "${in}" "${out}"
    # Optional sanity check:
    # cdo -s showname "${out}"
  done

  # 2) Merge into a single file containing 8 variables
  OUT="${OUTDIR}/livestock_density_${yr}.nc"
  echo "Merging -> ${OUT}"
  cdo -O merge "${INDIR}"/*_"${yr}".ren.nc "${OUT}"

  # 3) Verify variable names
  echo -n "Variables in output: "
  cdo -s showname "${OUT}"   # should list: buffalo cattle chicken duck goat horse pig sheep

  # (Optional) Clean up temporary renamed files
  rm -f "${INDIR}"/*_"${yr}".ren.nc

done

