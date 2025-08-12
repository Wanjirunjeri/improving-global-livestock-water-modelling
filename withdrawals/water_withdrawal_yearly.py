#!/usr/bin/env python
"""
Create ONE NetCDF per year (1980-2019) containing daily water-withdrawal
maps for all livestock species.

• temperature file      : $VSC_SCRATCH/era5land_daily/t2m_1980_2019.nc
• density file          : $VSC_HOME/GLWD/liv_density/Liv_Pop_1980_2019_regrid_con.nc
• output directory      : $VSC_SCRATCH/liv_wd_yearly/
"""
from pathlib import Path
import os
import xarray as xr
from water_withdrawal import withdrawal_by_gridcell

SCRATCH = Path(os.environ["VSC_SCRATCH"])
HOME    = Path(os.environ["VSC_HOME"])

T2M_FILE  = SCRATCH / "era5land_daily" / "t2m_1980_2019.nc"
DENS_FILE = HOME    / "GLWD" / "liv_density" / "Liv_Pop_1980_2019_counts_faoGrid.nc"      
OUT_DIR   = SCRATCH / "liv_wd_yearly_regrid"
OUT_DIR.mkdir(exist_ok=True)

# ── open temperature once (Kelvin→°C, rename dim) ───────────────────────────
t2m_all = xr.open_dataset(T2M_FILE, decode_times=True)
t2m_all = t2m_all.rename({"valid_time": "time"})
t2m_all = t2m_all["t2m"] #= t2m_all.t2m - 273.15   # °C

# ── open density file (annual steps) ────────────────────────────────────────
dens_ds = xr.open_dataset(DENS_FILE)
dens_ds = dens_ds.rename({"time": "year"})
dens_ds["year"] = dens_ds.year.astype("datetime64[ns]")

NAME_MAP = {                       # density var  →  animal keyword
    "CowPop":     "cattle",
    "BufalloPop": "buffalo",
    "GoatPop":    "goats",
    "SheepPop":   "sheep",
    "PigPop":     "pig",
    "ChickenPop": "chicken",
    "DuckPop":    "ducks",
    "HorsePop":   "horses",
}

compression = dict(zlib=True, complevel=4)

for yr in range(2019, 2020):
    print(f"🔹 Year {yr}",flush=True)
    outfile = OUT_DIR/ f"Liv2_WD_{yr}.nc"
    if outfile.exists():
        print(f"Year {yr} - output already exists, skipping.", flush=True)
        continue
    #t2m = t2m_all.t2m.sel(time=str(yr))

    t2m = t2m_all.sel(time=slice(f"{yr}-01-01", f"{yr}-12-31"))

    data_vars = []
    for var, animal in NAME_MAP.items():
        if var not in dens_ds:
            print(f"   ⚠️  {var} missing – skipped"); continue

        # 2) grab the 1-Jan map for this year and squeeze away the time dim
        dens_1jan = (dens_ds[var]
                     .sel(year=str(yr))               # picks that one time
                     .squeeze("year", drop=True))        # now dims=(lat,lon)

        # 3) broadcast to every day of the year
        dens_daily = dens_1jan.expand_dims(time=t2m.time)

        # 4) compute litres·cell⁻¹·day⁻¹ → convert to m³
        lpd = withdrawal_by_gridcell(animal, t2m, dens_daily)
        m3  = (lpd / 1000.0).rename(f"{animal.lower()}_wd")
        m3.attrs.update(
            units="m3 cell-1 day-1",
            long_name=f"{animal} drinking-water withdrawal",
        )

        """        
        dens_yearly = dens_ds[var].sel(year=slice("1980","2019"))

        # convert 'year' (1-Jan each year) → a *real* daily time axis
        dens_days = dens_yearly.interp(
            year=("time", t2m.time.dt.year)   # match each day’s calendar year
        ).drop_vars("year")                   # remove the leftover coordinate
        dens_days = dens_days.chunk({"time": 365, "lat": 180})

        m3 = (withdrawal_by_gridcell(animal, t2m, dens_daily) / 1000.0
            ).rename(f"{animal.lower()}_wd")
        m3.attrs.update(units="m3 cell-1 day-1",
                        long_name=f"{animal} drinking-water withdrawal")
        """
        
        data_vars.append(m3)

    ds_year = xr.merge(data_vars)
    out_file = OUT_DIR / f"Liv_WD_{yr}.nc"

    enc = {v: {"zlib": True, "complevel": 4} for v in ds_year.data_vars}

    """
    ds_year.to_netcdf(
        out_file,
        engine="netcdf4",          # or engine="h5netcdf"
        format="NETCDF4",          # makes the intention explicit
        encoding=enc,
    )

    """
    ds_year.to_netcdf(out_file,
                      encoding={v: compression for v in ds_year.data_vars})
    print(f"   ✔  written → {out_file}", flush=True)

print("🎉  All 40 files done:", OUT_DIR)




# 1. Are we skipping species?
for k in NAME_MAP:
    print(k, k in dens_ds)

# 2. Units & magnitudes
print(dens_ds["CowPop"].attrs)          # look for 'units'
print(float(dens_ds["CowPop"].mean()))  # typical heads/km² ?
print(dens_ds["CowPop"].isel(lat=..., lon=...))  # spot check

# 3. Temperature stats
print(float(t2m.mean()), float(t2m.min()), float(t2m.max()))

# 4. Final values range
print(ds_year.to_array().max().item(), ds_year.to_array().mean().item())

# 5. Compare LHS and RHS
test = withdrawal_by_gridcell("cattle", t2m.isel(time=0), dens_daily.isel(time=0))
print(test.sum().item())

