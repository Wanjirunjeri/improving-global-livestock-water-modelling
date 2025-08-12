#!/usr/bin/env python3
"""Plot generated vs harmonized livestock‑withdrawal bars for *specific* (lat, lon, year) points.

For each point you supply (lat, lon, year, label) the script:
1. Aggregates all *_wd variables at that grid cell (generated m³ day⁻¹) → km³ month⁻¹.
2. Converts the harmonized monthly‑mean m³ s⁻¹ values (withd_liv or total_withdrawal_livestock) → km³ month⁻¹.
3. Saves two bar charts under   plots3_<YEAR>/
   • bar_monthly_km3_<LABEL>_<lat>_<lon>_<YEAR>.png
   • bar_percent_diff_<LABEL>_<lat>_<lon>_<YEAR>.png
"""
import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# ------------------------------------------------------------------
# USER CONFIG ░░ Supply any points you like ░░
# (lat, lon, year, label)
POINTS = [
    (-3.4653, -62.2159, 1984, "Amazon_pt"),
    (-1.2921,   36.8219, 2005, "Nairobi_pt"),
]

GEN_TPL  = "/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid/Liv_WD_{year}.nc"
HARM_TPL = "/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock/withdrawal_livestock_m3_per_day_spatially_harmonized_using_Khan_et_al2023_weights_{year}.nc"

# ------------------------------------------------------------------
# Helper functions

def pick_harmonized_var(ds: xr.Dataset) -> str:
    for v in ("withd_liv", "total_withdrawal_livestock"):
        if v in ds.data_vars:
            return v
    raise ValueError("Expected 'withd_liv' or 'total_withdrawal_livestock' in harmonized dataset")


def fmt_sci_axis(ax):
    fmt = ScalarFormatter(useMathText=True)
    fmt.set_scientific(True)
    fmt.set_powerlimits((-3, 4))
    fmt.set_useOffset(False)
    ax.yaxis.set_major_formatter(fmt)


def jan_dec_frame():
    months = pd.DataFrame({"month_num": range(1, 13)})
    months["month"] = pd.to_datetime(months["month_num"], format="%m").dt.strftime("%b")
    return months

# Cache NetCDFs so we don’t reload for repeated years
GEN_CACHE, HARM_CACHE = {}, {}

for lat, lon, year, label in POINTS:
    outdir = f"/scratch/brussel/111/vsc11128/liv_wd_yearly/analysis/plots3_{year}"
    os.makedirs(outdir, exist_ok=True)

    # ---------- Load or retrieve datasets ----------
    if year not in GEN_CACHE:
        GEN_CACHE[year] = xr.open_dataset(GEN_TPL.format(year=year))
    gen_ds = GEN_CACHE[year]

    if year not in HARM_CACHE:
        HARM_CACHE[year] = xr.open_dataset(HARM_TPL.format(year=year))
    harm_ds = HARM_CACHE[year]

    harm_var = pick_harmonized_var(harm_ds)
    gen_vars = [v for v in gen_ds.data_vars if v.endswith("_wd")]
    if not gen_vars:
        raise ValueError(f"No *_wd variables in generated dataset for {year}")

    # ---------- Generated monthly km³ ----------
    gen_point_daily = sum(gen_ds[v].sel(lat=lat, lon=lon, method="nearest") for v in gen_vars)
    gen_monthly_km3 = gen_point_daily.resample(time="1ME").sum() / 1e9

    # ---------- Harmonized monthly km³ ----------
    harm_point = harm_ds[harm_var].sel(lat=lat, lon=lon, method="nearest")
    days_in_month = harm_point["time"].dt.days_in_month
    harm_monthly_km3 = (harm_point * xr.DataArray(days_in_month, coords=[harm_point["time"]], dims=["time"]) * 86400.0) / 1e9

    # ---------- Build tidy DataFrames ----------
    gdf = gen_monthly_km3.to_dataframe(name="Generated").reset_index()
    hdf = harm_monthly_km3.to_dataframe(name="Harmonized").reset_index()
    for df in (gdf, hdf):
        df["month_num"] = df["time"].dt.month
        df["month"] = df["time"].dt.strftime("%b")

    months = jan_dec_frame()
    g_plot = months.merge(gdf[["month_num", "Generated"]], on="month_num", how="left")
    h_plot = months.merge(hdf[["month_num", "Harmonized"]], on="month_num", how="left")

    # ---------- Plot bars km³/month ----------
    x = np.arange(12)
    w = 0.42
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w/2, g_plot["Generated"],   width=w, label="Generated",  color="tab:green", alpha=0.8)
    ax.bar(x + w/2, h_plot["Harmonized"],  width=w, label="Harmonized", color="tab:red",   alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(months["month"])
    ax.set_ylabel("km³ / month"); ax.set_xlabel("Month")
    ax.set_title(f"Monthly Withdrawal at ({lat}, {lon}) – {year} [{label}]")
    ax.legend(); ax.grid(axis="y", linestyle="--", alpha=0.5)
    fmt_sci_axis(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f"bar_monthly_km3_{label}_{lat}_{lon}_{year}.png"), dpi=300)
    plt.close()

    # ---------- Plot % difference bars ((H−G)/H) ----------
    pct = 100.0 * (h_plot["Harmonized"] - g_plot["Generated"]) / h_plot["Harmonized"].replace(0, np.nan)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(months["month"], pct, color="tab:blue", alpha=0.85)
    ax.axhline(0, color="k", lw=1)
    ax.set_ylabel("%")
    ax.set_xlabel("Month")
    ax.set_title(f"Percent Difference (H − G)/H at ({lat}, {lon}) – {year} [{label}]")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f"bar_percent_diff_{label}_{lat}_{lon}_{year}.png"), dpi=300)
    plt.close()

    # ---------- Console summary ----------
    print(f"✓ {label} {year}: generated {g_plot['Generated'].sum():.3e} km³/yr, "
          f"harmonized {h_plot['Harmonized'].sum():.3e} km³/yr → Δ {(h_plot['Harmonized'].sum()-g_plot['Generated'].sum()):.3e}")
    
