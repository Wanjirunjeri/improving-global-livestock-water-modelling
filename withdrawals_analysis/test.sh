#!/bin/bash

year=2015
infile=/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid/Liv_WD_${year}.nc

# 1️⃣ add all species into a single variable TOTAL (units unchanged)
cdo -L -expr,'TOTAL=cattle_wd+buffalo_wd+goats_wd+sheep_wd+pig_wd+chicken_wd+ducks_wd+horses_wd' \
    $infile tmp_total.nc

# 2️⃣ global sum over lat,lon  →  one time‑series, units m³ day⁻¹
cdo -L -fldsum tmp_total.nc global_daily_${year}.nc      # dims: time

# 3️⃣ annual total (timsum) and convert to km³
cdo -L -timsum global_daily_${year}.nc tmp_yearly_m3.nc  # still m³ yr⁻¹
cdo -L -divc,1e9 tmp_yearly_m3.nc global_annual_${year}_km3.nc

# 4️⃣ print the number
cdo outputtab,value global_annual_${year}_km3.nc
# → e.g.   32.74
rm tmp_total.nc tmp_yearly_m3.nc

