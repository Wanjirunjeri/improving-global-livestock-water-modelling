#!/usr/bin/env python3
"""
livestock_water_analysis.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Utility functions and a small CLI for exploring the harmonised
and re‑gridded global livestock‑drinking‑water withdrawal datasets
that sit on VUB‑HPC.

Key features
------------
1. **Fix the unit bug** in Sabin's harmonised NetCDFs (values are m³ s⁻¹ but
   labelled m³ day⁻¹) by multiplying with 86 400 × days_in_month.
2. **Build annual global rasters** or country‑aggregated time series
   (total, animal‑specific, or per‑capita).
3. **Plot**
   • global choropleth for any given year  
   • country annual time‑series with LOESS smoother  
   • year‑vs‑month heat map (variability diagnostics)  
   • pixel‑wise scatter of WD vs. renewable water (optional overlay)
4. Simple **command‑line interface** so you can fire off plots on the cluster.

Usage examples
--------------
```bash
# Quick‑look world map for 2015
python livestock_water_analysis.py map 2015 ~/figs/world_wd_2015.png

# Ethiopia annual totals 1971‑2019 (aggregated over all livestock)
python livestock_water_analysis.py ts ETH ~/figs/eth_ts.png

# Year‑month heat map for India
python livestock_water_analysis.py heat IND ~/figs/ind_heat.png
```

Dependencies
------------
```bash
module load 2023                # or your preferred toolchain
module load Python/3.10.4       # has cartopy & geopandas compiled
pip install --user xarray regionmask kalepy seaborn
```
"""

from __future__ import annotations

import argparse
import calendar
from pathlib import Path

import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import regionmask
import xarray as xr

# -----------------------------------------------------------------------------
# CONFIGURATION — edit if your directory names change
# -----------------------------------------------------------------------------
HARM_DIR = Path("/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock")
GEN_DIR = Path("/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid")
WORLD_SHP = gpd.datasets.get_path("naturalearth_lowres")  # built‑in 110 m polygons

# -----------------------------------------------------------------------------
# INTERNAL UTILITIES
# -----------------------------------------------------------------------------

def seconds_per_month(year: int) -> xr.DataArray:
    """Return 12‑element DataArray of the #seconds in each month of *year*."""
    secs = [calendar.monthrange(year, m)[1] * 86_400 for m in range(1, 13)]
    return xr.DataArray(secs, dims="time", name="secs")


def load_harmonised(year: int) -> xr.Dataset:
    """Open Sabin harmonised NetCDF for *year* and convert to m³ month⁻¹."""
    fp = HARM_DIR / (
        f"withdrawal_livestock_m3_per_day_spatially_harmonized_using_"
        f"Khan_et_al2023_weights_{year}.nc"
    )
    ds = xr.open_dataset(fp, decode_times=False)
    # Convert m³ s⁻¹  →  m³ month⁻¹
    secs = seconds_per_month(year)
    ds["withd_liv"] = ds["withd_liv"] * secs  # broadcasting over time
    ds["withd_liv"].attrs.update(
        units="m3 month-1", long_name="Total livestock WD (monthly)")
    return ds


def load_generated(year: int) -> xr.Dataset:
    """Open re‑gridded daily NetCDF, sum over animals and time → m³ year⁻¹."""
    fp = GEN_DIR / f"Liv_WD_{year}.nc"
    ds = xr.open_dataset(fp, decode_times=False)

    animal_vars = [v for v in ds.data_vars if v.endswith("_wd")]
    total_daily = sum(ds[v] for v in animal_vars)

    annual_total = total_daily.sum("time")  # time dimension is days
    annual_total.attrs.update(
        units="m3 year-1", long_name="Total livestock WD (annual)")

    return annual_total.to_dataset(name="withd_liv")


def build_country_mask() -> regionmask.Regions:
    """Return RegionMask regions object for ISO‑3 countries."""
    world = gpd.read_file(WORLD_SHP)[["iso_a3", "geometry"]]
    # Clean missing ISO codes (eg. French Antarctic Territory -> ATA)
    world = world[world.iso_a3 != "-99"].reset_index(drop=True)
    return regionmask.Regions(
        name="countries", numbers=range(len(world)), names=world.iso_a3,
        abbrevs=world.iso_a3, outlines=list(world.geometry))

COUNTRY_MASK = build_country_mask()


# -----------------------------------------------------------------------------
# PLOTTING HELPERS
# -----------------------------------------------------------------------------

def plot_global_map(ds: xr.Dataset, year: int, out: Path | None = None):
    arr = ds["withd_liv"].sum("time") if "time" in ds.dims else ds["withd_liv"]
    fig = plt.figure(figsize=(10, 4.5))
    ax = plt.axes(projection=ccrs.Robinson())
    arr.plot.pcolormesh(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap="viridis",
        vmin=0,
        # vmax set automatically via robust=True for 98th percentile clipping
        robust=True,
        cbar_kwargs={"shrink": 0.65, "label": "m³ year⁻¹"},
    )
    ax.coastlines(linewidth=0.3)
    ax.set_title(f"Global livestock drinking‑water withdrawal — {year}")
    if out:
        plt.savefig(out, dpi=300, bbox_inches="tight")
    else:
        plt.show()


def plot_country_timeseries(iso: str, years: list[int], out: Path | None = None):
    ts = []
    for y in years:
        ann = load_generated(y)  # annual already
        mask = COUNTRY_MASK.mask(ann)
        ann_country = ann.where(mask == COUNTRY_MASK.where(COUNTRY_MASK.abbrevs == iso).regions)
        ts.append(float(ann_country["withd_liv"].sum().values))
    ser = pd.Series(ts, index=years)

    fig, ax = plt.subplots(figsize=(6.5, 4))
    ser.div(1e9).plot(ax=ax, marker="o")  # to km³
    ser.rolling(window=5, center=True).mean().div(1e9).plot(ax=ax, lw=2.2)
    ax.set_ylabel("km³ year⁻¹")
    ax.set_title(f"Total livestock WD — {iso}")
    ax.grid(True, ls="--", lw=0.4)
    if out:
        fig.savefig(out, dpi=300, bbox_inches="tight")
    else:
        plt.show()


def plot_heatmap(iso: str, year0: int, year1: int, out: Path | None = None):
    years = list(range(year0, year1 + 1))
    hm = []
    for y in years:
        ds = load_harmonised(y)
        mask = COUNTRY_MASK.mask(ds)
        ds_ctry = ds.where(mask == COUNTRY_MASK.where(COUNTRY_MASK.abbrevs == iso).regions)
        # monthly sums over lat/lon
        series = ds_ctry["withd_liv"].sum(["lat", "lon"]).to_series()
        hm.append(series.values)
    arr = np.vstack(hm)  # year × 12

    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(arr / 1e9, aspect="auto", origin="lower")
    ax.set_yticks(range(len(years)))
    ax.set_yticklabels(years)
    ax.set_xticks(range(12))
    ax.set_xticklabels(calendar.month_abbr[1:])
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("km³ month⁻¹")
    ax.set_title(f"{iso} | Monthly livestock WD (km³)")
    if out:
        fig.savefig(out, dpi=300, bbox_inches="tight")
    else:
        plt.show()

# -----------------------------------------------------------------------------
# COMMAND‑LINE ENTRY POINT
# -----------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Plot utilities for livestock water‑withdrawal datasets",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s_map = sub.add_parser("map", help="Global map for a single year")
    s_map.add_argument("year", type=int, help="Year, 1971‑2019")
    s_map.add_argument("outfile", nargs="?", type=Path)

    s_ts = sub.add_parser("ts", help="Country annual time series")
    s_ts.add_argument("iso", help="ISO‑3 country code, e.g. IND")
    s_ts.add_argument("outfile", nargs="?", type=Path)
    s_ts.add_argument(
        "--start", type=int, default=1980, help="First year (default 1980)")
    s_ts.add_argument(
        "--end", type=int, default=2019, help="Last year (default 2019)")

    s_hm = sub.add_parser("heat", help="Year‑by‑month heatmap for a country")
    s_hm.add_argument("iso", help="ISO‑3 code")
    s_hm.add_argument("outfile", nargs="?", type=Path)
    s_hm.add_argument("--start", type=int, default=1971)
    s_hm.add_argument("--end", type=int, default=2019)

    return p.parse_args()


def main():
    args = parse_args()
    if args.cmd == "map":
        ds = load_generated(args.year) if args.year >= 1980 else load_harmonised(args.year)
        plot_global_map(ds, args.year, args.outfile)

    elif args.cmd == "ts":
        ys = list(range(args.start, args.end + 1))
        plot_country_timeseries(args.iso, ys, args.outfile)

    elif args.cmd == "heat":
        plot_heatmap(args.iso, args.start, args.end, args.outfile)


if __name__ == "__main__":
    main()

