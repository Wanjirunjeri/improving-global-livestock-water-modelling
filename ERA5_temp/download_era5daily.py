import cdsapi, pathlib, os

c = cdsapi.Client()

years   = range(1971, 2021)
months  = [f"{m:02d}" for m in range(1, 13)]
days    = [f"{d:02d}" for d in range(1, 32)]

# choose your scratch path
scratch = pathlib.Path("/scratch/brussel/111/vsc11128/era5land_daily")
scratch.mkdir(parents=True, exist_ok=True)

for y in years:
    for m in months:
        target = scratch / f"era5land_t2m_dailymean_{y}.nc"
        if target.exists():
            print(target.name, "already done"); continue

        c.retrieve(
          "derived-era5-land-daily-statistics",
            {
                "variable"       : ["2m_temperature"],
                "year"           : str(y),
                "month"          : str(m),
                "day"            : days,
                "daily_statistic": "daily_mean",
                "time_zone"      : "utc+00:00",
                "frequency"      : "1_hourly",
                "data_format"    : "netcdf",
              "download_format": "unarchived"
            },
            str(target)
        )
        print("✓", target.name, "saved to scratch")

