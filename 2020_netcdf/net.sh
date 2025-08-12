#!/usr/bin/env bash
set -euo pipefail



TIF="${VSC_SCRATCH}/fao_validation/2020_netcdf/GLW4-2020.D-DA.GLEAM3-ALL-LU.tif"
OUT="${VSC_SCRATCH}/fao_validation/2020_netcdf"
OUTMERGE="${VSC_SCRATCH}/fao_validation/2020_out_netcdf"
mkdir -p "$OUT" "$OUTMERGE"

# 1) GeoTIFF → NetCDF (variable is 'Band1')
gdal_translate -of netCDF "$TIF" "$OUT/all_2020_density.nc"

# 2) Rename Band1 → total_density (still head/km^2)
cdo -O chname,Band1,total_density "$OUT/all_2020_density.nc" "$OUT/all_2020_density.ren.nc"

# 3) Cell area (m^2 → km^2)
cdo -O gridarea "$OUT/all_2020_density.ren.nc" "$OUT/area_m2.nc"
cdo -O expr,'cell_area=cell_area/1e6' "$OUT/area_m2.nc" "$OUT/area_km2.nc"

# 4) Convert density → counts per cell (head/cell)
cdo -O merge "$OUT/all_2020_density.ren.nc" "$OUT/area_km2.nc" "$OUT/tmp.nc"
cdo -O expr,'total=total_density*cell_area' "$OUT/tmp.nc" "$OUTMERGE/livestock_counts_total_2020.nc"
rm -f "$OUT/tmp.nc"

echo "Created: $OUTMERGE/livestock_counts_total_2020.nc  (total head/cell)"

