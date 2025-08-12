#!/usr/bin/env bash
set -euo pipefail

# Load tools (adjust if your cluster uses different module names)
#module load GDAL
#module load CDO

IN="${VSC_SCRATCH}/fao_validation/2020_netcdf"
OUT="${VSC_SCRATCH}/fao_validation/2020_netcdf"
OUTMERGE="${VSC_SCRATCH}/fao_validation/2020_out_netcdf"
mkdir -p "$OUTMERGE"

# Map GLW4 codes to species; NO SPACES around '='
declare -A TIF=(
  [buffalo]="${IN}/GLW4-2020.D-DA.BFL.tif"
  [cattle]="${IN}/GLW4-2020.D-DA.CTL.tif"
  [chicken]="${IN}/GLW4-2020.D-DA.CHK.tif"
  [goat]="${IN}/GLW4-2020.D-DA.GTS.tif"
  [pig]="${IN}/GLW4-2020.D-DA.PGS.tif"
  [sheep]="${IN}/GLW4-2020.D-DA.SHP.tif"
)

echo "→ Converting GeoTIFFs to NetCDF and renaming variables…"
for sp in buffalo cattle chicken goat pig sheep; do
  tif="${TIF[$sp]}"
  [[ -f "$tif" ]] || { echo "ERROR: missing $tif"; exit 2; }

  # 1) GeoTIFF -> NetCDF (density: head/km^2)
  gdal_translate -of netCDF "$tif" "$OUT/${sp}_2020.nc"

  # 2) Rename variable Band1 -> <species>
  cdo -O chname,Band1,${sp} "$OUT/${sp}_2020.nc" "$OUT/${sp}_2020.ren.nc"
done

echo "→ Merging six species (densities) -> ${OUTMERGE}/livestock_density_2020.nc"
cdo -O merge "$OUT"/{buffalo,cattle,chicken,goat,pig,sheep}_2020.ren.nc \
    "$OUTMERGE/livestock_density_2020.nc"

# Build cell areas and convert densities (head/km^2) -> counts/cell
echo "→ Converting densities to counts per cell…"
cdo -O gridarea "$OUTMERGE/livestock_density_2020.nc" "$OUTMERGE/area_m2.nc"
cdo -O expr,'cell_area=cell_area/1e6' "$OUTMERGE/area_m2.nc" "$OUTMERGE/area_km2.nc"
cdo -O merge "$OUTMERGE/livestock_density_2020.nc" "$OUTMERGE/area_km2.nc" "$OUTMERGE/tmp_merge.nc"
cdo -O expr,'buffalo=buffalo*cell_area; cattle=cattle*cell_area; chicken=chicken*cell_area; goat=goat*cell_area; pig=pig*cell_area; sheep=sheep*cell_area' \
    "$OUTMERGE/tmp_merge.nc" "$OUTMERGE/livestock_counts_2020.nc"
rm -f "$OUTMERGE/tmp_merge.nc"

echo "Done."
echo "  DENSITY (head/km^2): ${OUTMERGE}/livestock_density_2020.nc"
echo "  COUNTS  (head/cell): ${OUTMERGE}/livestock_counts_2020.nc   <-- use this for validation"

