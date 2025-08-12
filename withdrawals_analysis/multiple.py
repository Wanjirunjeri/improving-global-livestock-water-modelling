#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import xarray as xr

# ---------------- CONFIG ----------------
years = [ 2005]  # add as many as you need
# (lat, lon, label) tuples — label is only for filenames/titles
points = [
    (-3.4653, -62.2159, "pt1_Amazon")
]

gen_tpl  = "/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid/Liv_WD_{year}.nc"
harm_tpl = "/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock/" \
           "withdrawal_livestock_m3_per_day_spatially_harmonized_using_Khan_et_al2023_weights_{year}.nc"

# ---------------- HELPERS ----------------
def pick_harmonized_var(ds: xr.Dataset) -> str:
    for v in ("withd_liv", "total_withdrawal_livestock"):
        if v in ds.data_vars:
            return v
    raise ValueError("Harmonized dataset variable not found: tried 'withd_liv' and 'total_withdrawal_livestock'.")

def species_vars(ds: xr.Dataset):
    vs = [v for v in ds.data_vars if v.endswith("_wd")]
    if not vs:
        raise ValueError("No '*_wd' variables found in generated dataset.")
    return vs

def ensure_outdir(path):
    os.makedirs(path, exist_ok=True)

def jan_dec_frame():
    m = pd.DataFrame({"month_num": range(1, 13)})
    m["month"] = pd.to_datetime(m["month_num"], format="%m").dt.strftime("%b")
    return m

def fmt_sci_axis(ax):
    fmt = ScalarFormatter(useMathText=True)
    fmt.set_scientific(True)
    fmt.set_powerlimits((-3, 4))
    fmt.set_useOffset(False)
    ax.yaxis.set_major_formatter(fmt)

# ---------------- MAIN ----------------
for year in years:
    outdir = f"/scratch/brussel/111/vsc11128/liv_wd_yearly/analysis/plots3_{year}"
    ensure_outdir(outdir)

    gen_path  = gen_tpl.format(year=year)
    harm_path = harm_tpl.format(year=year)

    # Load once per year
    gen_ds  = xr.open_dataset(gen_path)
    harm_ds = xr.open_dataset(harm_path)
    harm_var = pick_harmonized_var(harm_ds)
    gen_vars = species_vars(gen_ds)

    for (lat, lon, label) in points:
        # ------------ GENERATED: monthly km³ ------------
        gen_point_daily = sum(gen_ds[v].sel(lat=lat, lon=lon, method="nearest") for v in gen_vars)  # m3/day
        # resample to month-end ("1ME") to match your earlier method
        gen_monthly_km3 = gen_point_daily.resample(time="1MS").sum() / 1e9
        gen_lat = float(gen_point_daily["lat"])
        gen_lon = float(gen_point_daily["lon"])

        gdf = gen_monthly_km3.to_dataframe(name="Generated_km3").reset_index()
        gdf["month"]     = gdf["time"].dt.strftime("%b")
        gdf["month_num"] = gdf["time"].dt.month
        gdf = gdf.sort_values("month_num")

        # ------------ HARMONIZED: monthly km³ ------------
        harm_point = harm_ds[harm_var].sel(lat=lat, lon=lon, method="nearest")  # m3/s, monthly mean
        harm_lat = float(harm_point["lat"])
        harm_lon = float(harm_point["lon"])

        # monthly mean m3/s -> m3/month
        time_index = harm_point["time"].to_index()
        days_in_month = time_index.days_in_month
        harm_monthly_km3 = (harm_point * xr.DataArray(days_in_month, coords=[harm_point["time"]], dims=["time"]) * 86400.0) / 1e9

        hdf = harm_monthly_km3.to_dataframe(name="Harmonized_km3").reset_index()
        hdf["month"]     = hdf["time"].dt.strftime("%b")
        hdf["month_num"] = hdf["time"].dt.month
        hdf = hdf.sort_values("month_num")

        # ------------ Align by calendar month ------------
        months = jan_dec_frame()
        g_plot = months.merge(gdf[["month_num", "Generated_km3"]], on="month_num", how="left")
        h_plot = months.merge(hdf[["month_num", "Harmonized_km3"]], on="month_num", how="left")

        # ------------ Print sanity info ------------
        print(f"[{year} | {label}] Generated sampled at ({gen_lat:.3f}, {gen_lon:.3f}); "
              f"Harmonized sampled at ({harm_lat:.3f}, {harm_lon:.3f})")
        print(f"  Annual totals at this cell (km³/yr): "
              f"G={g_plot['Generated_km3'].sum():.6e}, H={h_plot['Harmonized_km3'].sum():.6e}")

        # ------------ Plot 1: side-by-side bars (km³/month) ------------
        x = np.arange(len(months))
        w = 0.42
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x - w/2, g_plot["Generated_km3"], width=w, label="Generated",  alpha=0.8, color="tab:green")
        ax.bar(x + w/2, h_plot["Harmonized_km3"], width=w, label="Harmonized", alpha=0.8, color="tab:red")
        ax.set_xticks(x); ax.set_xticklabels(months["month"])
        ax.set_title(f"Monthly Withdrawal at ({lat}, {lon}) – {year} [{label}]")
        ax.set_ylabel("km³ / month"); ax.set_xlabel("Month")
        ax.legend(); ax.grid(axis="y", linestyle="--", alpha=0.5)
        fmt_sci_axis(ax)
        plt.tight_layout()
        fname1 = os.path.join(outdir, f"bar_monthly_km3_{label}_{lat}_{lon}_{year}.png")
        plt.savefig(fname1, dpi=300)
        plt.close()

        # ------------ Plot 2: percent-difference bars ((H−G)/H) ------------
        pct = 100.0 * (h_plot["Harmonized_km3"] - g_plot["Generated_km3"]) / h_plot["Harmonized_km3"].replace(0, np.nan)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(months["month"], pct, color="tab:blue", alpha=0.85)
        ax.axhline(0, color="k", lw=1)
        ax.set_title(f"Percent Difference (H − G)/H at ({lat}, {lon}) – {year} [{label}]")
        ax.set_ylabel("%"); ax.set_xlabel("Month")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        fname2 = os.path.join(outdir, f"bar_percent_diff_{label}_{lat}_{lon}_{year}.png")
        plt.savefig(fname2, dpi=300)
        plt.close()

