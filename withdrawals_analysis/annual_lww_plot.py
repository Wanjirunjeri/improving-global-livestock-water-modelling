from pathlib import Path
import re
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt

# 1. CONFIGURATION -----------------------------------------------------
DATA_DIR    = Path("/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid")
PATTERN     = "Liv_WD_*.nc"
CHUNKS      = {"time": 12}
FIGURE_FILE = Path("annual_global_withdrawal_km3.png")

# 2. COMPUTE YEARLY TOTALS --------------------------------------------
records = []

for f in sorted(DATA_DIR.glob(PATTERN)):
    m = re.search(r"_(\d{4})\.nc$", f.name)
    if not m:
        print(f"⚠ Skipping {f.name}: no year found")
        continue
    year = int(m.group(1))

    with xr.open_dataset(f, chunks=CHUNKS) as ds:
        # all *_wd variables for livestock
        wd_vars = [v for v in ds.data_vars if v.endswith("_wd")]
        if not wd_vars:
            raise ValueError(f"No *_wd variables found in {f.name}")
        
        annual_total = sum(
            ds[var]
            .sum(dim=["lat", "lon"])   # spatial sum
            .sum(dim="time")           # sum over 365/366 days
            for var in wd_vars
        ).compute()

        records.append({"year": year, "km3": float(annual_total) / 1e9})

# 3. BUILD DATAFRAME ---------------------------------------------------
df = pd.DataFrame(records).sort_values("year")
print(df)

# 4. PLOT --------------------------------------------------------------
plt.figure(figsize=(10, 5))
plt.plot(df["year"], df["km3"], color="blue", lw=1.5)
plt.xlabel("Year")
plt.ylabel("Global livestock withdrawal (km³ year⁻¹)")
plt.title("Annual Global Livestock Drinking-Water Withdrawal")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(FIGURE_FILE, dpi=300)

print(f"✓ Yearly totals figure written → {FIGURE_FILE.resolve()}")

