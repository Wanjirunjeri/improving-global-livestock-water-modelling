# ──────────────────────────────────────────────────────────────────────
# monthly_global_livestock_withdrawal.py
# ──────────────────────────────────────────────────────────────────────
from pathlib import Path
import re
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt

# ---------- styling (safe defaults) ----------
plt.rcParams.update({
    "axes.titlesize": 19,
    "axes.labelsize": 16,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
})


# 1. CONFIGURATION -----------------------------------------------------
DATA_DIR    = Path("/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid")
PATTERN     = "Liv_WD_*.nc"            # matches Liv_WD_1980.nc … 2019.nc
CHUNKS      = {"time": 12}             # lazy-load one year at a time
FIGURE_FILE = Path("monthly_global_withdrawal_km3.png")

# 2. BUILD MONTHLY GLOBAL TOTALS --------------------------------------
records = []                           # (datetime, km³) rows go here

for f in sorted(DATA_DIR.glob(PATTERN)):
    m = re.search(r"_(\d{4})\.nc$", f.name)
    if not m:
        print(f"⚠  Skipping {f.name}: no YYYY found"); continue

    with xr.open_dataset(f, chunks=CHUNKS) as ds:
        # all variables that represent withdrawals (…_wd)
        wd_vars = [v for v in ds.data_vars if v.endswith("_wd")]
        if not wd_vars:
            raise ValueError(f"No *_wd variables in {f.name}")

        # days-per-timestep (xarray decodes ‘time’ automatically)
        days_in_month = ds["time"].dt.days_in_month

        # m³ day⁻¹  →  m³ month⁻¹ ; then sum over space & species
        monthly_tot = sum(
            (ds[var] * days_in_month)          # per cell, per month
            .sum(dim=["lat", "lon"])           # global
            for var in wd_vars
        ).compute()                            # bring result into memory

        # store each month’s value
        for i, t in enumerate(monthly_tot.time.values):
            records.append(
                {"date": pd.to_datetime(str(t)),
                 "km3":  float(monthly_tot[i]) / 1e9}   # m³ → km³
            )
"""
# 3. PLOT --------------------------------------------------------------
df = pd.DataFrame(records).sort_values("date")

plt.figure(figsize=(12, 6))
plt.plot(df["date"], df["km3"], color="blue", lw=1.0)
plt.xlabel("Year")
plt.ylabel("Global livestock withdrawal (km³ month⁻¹)")
plt.title("Monthly Global Livestock Drinking-Water Withdrawal")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(FIGURE_FILE, dpi=300)

print(f"✓ Figure written → {FIGURE_FILE.resolve()}")
"""
# 4. GROUP BY YEAR AND PLOT YEARLY TOTALS --------------------------------
df["year"] = df["date"].dt.year
annual_df = df.groupby("year")["km3"].sum().reset_index()

plt.figure(figsize=(10, 5))
plt.plot(annual_df["year"], annual_df["km3"], color="blue", lw=1.5)
plt.xlabel("Year")
plt.ylabel("Global livestock withdrawal (km³ year⁻¹)")
plt.title("Annual Global Livestock Drinking-Water Withdrawal")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("annual_global_withdrawal_km3.png", dpi=300)

print("✓ Yearly totals figure written → annual_global_withdrawal_km3.png")
