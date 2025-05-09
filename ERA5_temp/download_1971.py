#!/usr/bin/env python
import cdsapi
import os, pathlib

# ----------------------------------------------------------------------
# 1.  WHERE TO SAVE  (your private scratch path, e.g. /scratch/brussel/111/vsc11128)
# ----------------------------------------------------------------------
scratch_root = pathlib.Path("/scratch/brussel/111/vsc11128/era5land_daily")
scratch_root.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 2.  WHAT TO DOWNLOAD  (all months of 1971 – change years as needed)
# ----------------------------------------------------------------------
#"1982", "1983", "1984", "1985", "1986",
#        "1987", "1988", "1989", "1990", "1991", "1992", "1993", "1994", "1995",
#        "1996", "1997", "1998", "1999", "2000"


years  = [ "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999", "2000"] 
months = [f"{m:02d}" for m in range(1, 13)]
days   = [f"{d:02d}" for d in range(1, 32)]   # harmless extras ignored

dataset = "derived-era5-land-daily-statistics"

# ----------------------------------------------------------------------
# 3.  DOWNLOAD LOOP  (one NetCDF ≈ 35 MB per month)
# ----------------------------------------------------------------------
c = cdsapi.Client(retry_max=30, sleep_max=300)

for y in years:
    for m in months:
        target = scratch_root / f"era5land_t2m_dailymean_{y}_{m}.nc"
        if target.exists():
            print(target.name, "already present – skipping")
            continue

        c.retrieve(
            dataset,
            {
                "variable"       : ["2m_temperature"],
                "year"           : y,
                "month"          : m,
                "day"            : days,
                "daily_statistic": "daily_mean",
                "time_zone"      : "utc+00:00",
                "frequency"      : "1_hourly",
                "data_format"    : "netcdf",
                "download_format": "unarchived"
            },
            str(target)                         # write straight to scratch
        )
        print("✓", target.name, "saved")

print("All requested months finished.")

