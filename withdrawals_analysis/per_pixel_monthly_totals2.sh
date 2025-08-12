import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import xarray as xr

# ---------------- CONFIG ----------------
year = 2005
outdir = f"/scratch/brussel/111/vsc11128/liv_wd_yearly/analysis/plots3_{year}"
os.makedirs(outdir, exist_ok=True)

gen_path  = f"/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid/Liv_WD_{year}.nc"
harm_path = f"/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock/withdrawal_livestock_m3_per_day_spatially_harmonized_using_Khan_et_al2023_weights_{year}.nc"

# Point to sample (lat, lon)
target_lat = -3.4653
target_lon = -62.2159

# -------------- LOAD --------------------
gen_ds   = xr.open_dataset(gen_path)       # generated: m3/cell/day, many *_wd variables
harm_ds  = xr.open_dataset(harm_path)      # harmonized: monthly mean m3/s

# -------------- GENERATED: monthly km³ ----------------
# Sum all species at the nearest grid cell, then sum over days per month
species_vars = [v for v in gen_ds.data_vars if v.endswith("_wd")]
if not species_vars:
    raise ValueError("No *_wd variables in generated dataset")

gen_point_daily = sum(
    gen_ds[v].sel(lat=target_lat, lon=target_lon, method="nearest")
    for v in species_vars
)  # m3/day at that cell

# monthly totals (m3/month) -> km3/month
gen_monthly_km3 = gen_point_daily.resample(time="MS").sum() / 1e9
# keep the actual sampled coords to report
gen_lat = float(gen_point_daily["lat"])
gen_lon = float(gen_point_daily["lon"])

# -------------- HARMONIZED: monthly km³ ----------------
# pick the variable robustly
harm_var_candidates = ["withd_liv", "total_withdrawal_livestock"]
harm_var = None
for v in harm_var_candidates:
    if v in harm_ds.data_vars:
        harm_var = v
        break
if harm_var is None:
    raise ValueError(f"None of {harm_var_candidates} found in harmonized dataset")

harm_point_m3s = harm_ds[harm_var].sel(lat=target_lat, lon=target_lon, method="nearest")
harm_lat = float(harm_point_m3s["lat"])
harm_lon = float(harm_point_m3s["lon"])

# Convert monthly mean m3/s -> m3/month by multiplying with seconds in that month
days_in_month = harm_point_m3s["time"].dt.days_in_month
harm_monthly_km3 = (harm_point_m3s * days_in_month * 86400.0) / 1e9

# -------------- ALIGN + DATAFRAME ----------------
# Use the same monthly index (start-of-month) and inner-join months present in both
g = gen_monthly_km3.to_series().rename("Generated_km3").reset_index()
h = harm_monthly_km3.to_series().rename("Harmonized_km3").reset_index()

# Normalize time to month-start for both (guard against end-of-month stamps)
g["time"] = pd.to_datetime(g["time"]).dt.to_period("M").dt.to_timestamp("MS")
h["time"] = pd.to_datetime(h["time"]).dt.to_period("M").dt.to_timestamp("MS")

df = (g.merge(h, on="time", how="inner")
        .assign(month=lambda x: x["time"].dt.strftime("%b"),
                month_num=lambda x: x["time"].dt.month)
        .sort_values("month_num"))

# -------------- PRINT CHECKS ----------------
print(f"Sampled generated at (lat, lon): ({gen_lat:.3f}, {gen_lon:.3f})")
print(f"Sampled harmonized at (lat, lon): ({harm_lat:.3f}, {harm_lon:.3f})")
print("Annual totals at this cell (km³/year):")
print(f"  Generated:  {df['Generated_km3'].sum():.6e}")
print(f"  Harmonized: {df['Harmonized_km3'].sum():.6e}")

# -------------- BAR PLOT: km³/month (side-by-side) ----------------
x = np.arange(len(df))
w = 0.4

fig, ax = plt.subplots(figsize=(10,5))
ax.bar(x - w/2, df["Generated_km3"], width=w, label="Generated", alpha=0.7, color="tab:green")
ax.bar(x + w/2, df["Harmonized_km3"], width=w, label="Harmonized", alpha=0.7, color="tab:red")

ax.set_xticks(x)
ax.set_xticklabels(df["month"], rotation=0)
ax.set_title(f"Monthly Withdrawal at ({target_lat}, {target_lon}) – {year}")
ax.set_ylabel("km³ / month")
ax.set_xlabel("Month")
ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.5)

# Use scientific y-axis formatting if needed
fmt = ScalarFormatter(useMathText=True)
fmt.set_scientific(True); fmt.set_powerlimits((-3, 4)); fmt.set_useOffset(False)
ax.yaxis.set_major_formatter(fmt)

plt.tight_layout()
plt.savefig(os.path.join(outdir, f"bar_monthly_km3_{target_lat}_{target_lon}_{year}.png"), dpi=300)
plt.close()

# -------------- BAR PLOT: percent difference (H − G)/H ----------------
# Positive bar → Harmonized > Generated
df["PctDiff"] = 100.0 * (df["Harmonized_km3"] - df["Generated_km3"]) / df["Harmonized_km3"].replace(0, np.nan)

fig, ax = plt.subplots(figsize=(10,5))
ax.bar(df["month"], df["PctDiff"], color="tab:blue", alpha=0.8)
ax.axhline(0, color="k", lw=1)
ax.set_title(f"Percent Difference (H − G)/H at ({target_lat}, {target_lon}) – {year}")
ax.set_ylabel("%")
ax.set_xlabel("Month")
ax.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(outdir, f"bar_percent_diff_{target_lat}_{target_lon}_{year}.png"), dpi=300)
plt.close()

