
"""
Global livestock water‑withdrawal time series
--------------------------------------------
• Reads monthly NetCDF files containing m³ day⁻¹ values.
• Converts them to m³ month⁻¹ (multiplying by the month length).
• Aggregates to annual global totals (km³ yr⁻¹) and saves a PNG plot.
"""

# ---------------------------------------------------------------------
# 0. Use a headless backend before importing pyplot
# ---------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")           # <<< non‑GUI (OK on any HPC)
import matplotlib.pyplot as plt

import re
from pathlib import Path
import xarray as xr
import pandas as pd

# ---------------------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------------------
DATA_DIR     = Path("/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock")
PATTERN      = "withdrawal_*.nc"
VAR_NAME     = "withd_liv"              # fallback handled below
CHUNKS       = {"time": 12}
FIGURE_PATH  = Path("livestock_withdrawal_km3yr.png")  # output

# ---------------------------------------------------------------------
# 2. GATHER FILES & COMPUTE
# ---------------------------------------------------------------------
records = []
for f in sorted(DATA_DIR.glob(PATTERN)):
    m = re.search(r"_(\d{4})\.nc$", f.name)
    if not m:
        print(f"⚠  Skipping {f.name}: no YYYY found")
        continue
    year = int(m.group(1))

    with xr.open_dataset(f, chunks=CHUNKS) as ds:
        var = VAR_NAME if VAR_NAME in ds.data_vars else list(ds.data_vars)[0]

        # m³ day⁻¹  →  m³ month⁻¹
        days_in_month = xr.DataArray(
            ds["time"].dt.days_in_month,
            coords={"time": ds["time"]},
            dims="time",
        )
        monthly_m3 = ds[var] * days_in_month*86400

        annual_m3 = (
            monthly_m3
            .sum(dim=["lat", "lon"])   # spatial
            .sum(dim="time")           # temporal
            .compute()
        )

    records.append((year, float(annual_m3) / 1e9))   # km³
 #   records.append((month, float(monthly_m3) / 1e9))

# ---------------------------------------------------------------------
# 3. DATAFRAME & PLOT
# ---------------------------------------------------------------------
df = pd.DataFrame(records, columns=["year", "km3"]).sort_values("year")
print(df)

plt.figure(figsize=(10, 5))
plt.plot(df["year"], df["km3"], color="blue")
plt.xlabel("Year")
plt.ylabel("Global livestock withdrawal (km³ yr⁻¹)")
plt.title("Harmonized global livestock water withdrawal by year")
plt.grid(True)
plt.tight_layout()

# ---------------------------------------------------------------------
# 4. SAVE FIGURE
# ---------------------------------------------------------------------
plt.savefig(FIGURE_PATH, dpi=300)
plt.close()           # good hygiene on batch nodes
#print(f"Figure saved → {FIGUREcolor="blue"_PATH.resolve()}")

# ---------------------------------------------------------------------
# 3. DATAFRAME & PLOT
# ---------------------------------------------------------------------
"""
df = pd.DataFrame(records, columns=["month", "km3"]).sort_values("month")
print(df)

plt.figure(figsize=(10, 5))
plt.plot(df["month"], df["km3"], color="blue")
plt.xlabel("Year")
plt.ylabel("Global livestock withdrawal (km³ month⁻¹)")
plt.title("Harmonized global livestock water withdrawal by month")
plt.tight_layout()

# ---------------------------------------------------------------------
# 4. SAVE FIGURE
# ---------------------------------------------------------------------
plt.savefig(Path("monthly graph"), dpi=300)
plt.close()           # good hygiene on batch nodes
"""
