from pathlib import Path
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import re

# ---------- styling (safe defaults) ----------
plt.rcParams.update({
    "axes.titlesize": 16,
    "axes.labelsize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
})


# ---------------------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------------------
DATA_DIR     = Path("/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock")
PATTERN      = "withdrawal_*.nc"
VAR_NAME     = "withd_liv"              # fallback handled below
CHUNKS       = {"time": 12}
FIGURE_PATH  = Path("monthly_livestock_withdrawal_km3_month.png")  # output

# ---------------------------------------------------------------------
# 2. GATHER FILES & COMPUTE
# ---------------------------------------------------------------------
records = []
for f in sorted(DATA_DIR.glob(PATTERN)):
    m = re.search(r"_(\d{4})\.nc$", f.name)
    if not m:
        print(f"⚠ Skipping {f.name}: no YYYY found")
        continue
    year = int(m.group(1))

    with xr.open_dataset(f, chunks=CHUNKS) as ds:
        var = VAR_NAME if VAR_NAME in ds.data_vars else list(ds.data_vars)[0]

        # m³/day → m³/month
        days_in_month = ds["time"].dt.days_in_month
        monthly_m3 = ds[var] * days_in_month * 86400

        # Sum over space (lat/lon)
        monthly_total = monthly_m3.sum(dim=["lat", "lon"]).compute()

        for i, time_val in enumerate(monthly_total["time"].values):
            date = pd.to_datetime(str(time_val))
            records.append((date, float(monthly_total[i]) / 1e9))  # km³

# ---------------------------------------------------------------------
# 3. DATAFRAME & PLOT
# ---------------------------------------------------------------------
df = pd.DataFrame(records, columns=["date", "km3"]).sort_values("date")
print(df)

plt.figure(figsize=(12, 6))
plt.plot(df["date"], df["km3"], lw=1)
plt.xlabel("Year")
plt.ylabel("Global livestock withdrawal (km³/month)")
plt.title("Monthly Harmonized Global Livestock Water Withdrawal (km³/month)")
plt.grid(True)
plt.tight_layout()
plt.savefig(FIGURE_PATH)

