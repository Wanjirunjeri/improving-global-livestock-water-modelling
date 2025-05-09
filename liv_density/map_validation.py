#!/usr/bin/env python3
"""
Validate Utrecht livestock density maps (re-gridded) against FAO maps.
Outputs:
   • validation_summary.csv
   • plots/{scatter_,diff_map_}<animal>_<year>.png
"""

import os, sys, numpy as np, xarray as xr, pandas as pd, matplotlib.pyplot as plt

# ─── 0. CONFIGURATION ────────────────────────────────────────────────────
UTRECHT_FILE     = "Liv_Pop_1980_2019_regrid_con.nc"

FAO_DIR_PREFIX   = "fao_density_renamed"   # will become fao_renamed_2010, _2015, ...
YEARS            = [2010, 2015]
ANIMALS          = ["cattle","buffalo","sheep","goat","horse","pig","chicken","duck"]

PLOT_DIR         = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# Utrecht → FAO variable renames
RENAME_MAP = {
    "BufalloPop": "buffalo",
    "ChickenPop": "chicken",
    "CowPop"    : "cattle",
    "DuckPop"   : "duck",
    "GoatPop"   : "goat",
    "HorsePop"  : "horse",
    "PigPop"    : "pig",
    "SheepPop"  : "sheep",
}

# ─── 1. LOAD & RENAME UTRECHT DATASET ────────────────────────────────────
print("📥  Opening Utrecht NetCDF …")
try:
    ds_utrecht = xr.open_dataset(UTRECHT_FILE)
except FileNotFoundError:
    sys.exit(f"❌  {UTRECHT_FILE} not found – run the regridding step first.")

present_map = {old:new for old,new in RENAME_MAP.items() if old in ds_utrecht.data_vars}
ds_utrecht  = ds_utrecht.rename(present_map)
print("✅  Variables after rename:", list(ds_utrecht.data_vars))

# ─── 2. VALIDATION LOOP ─────────────────────────────────────────────────
metrics = []

for animal in ANIMALS:
    if animal not in ds_utrecht.data_vars:
        print(f"⚠️  Utrecht lacks '{animal}' – skipping.")
        continue

    for year in YEARS:
        fao_dir  = f"{FAO_DIR_PREFIX}_{year}"
        fao_file = f"{fao_dir}/fao_{animal}_{year}.nc"

        if not os.path.isfile(fao_file):
            print(f"⚠️  Missing {fao_file} – skipping {animal} {year}.")
            continue

        print(f"🔍  {animal.capitalize()} {year}")

        fao = xr.open_dataset(fao_file)["population_density"]
        utrecht_slice = ds_utrecht[animal]
        if "time" in utrecht_slice.dims:
            utrecht_slice = utrecht_slice.sel(time=str(year), method="nearest")
        elif "year" in utrecht_slice.coords:
            utrecht_slice = utrecht_slice.sel(year=year)

        utrecht_masked = utrecht_slice.where(~np.isnan(fao))

        diff = utrecht_masked - fao
        rmse = float(np.sqrt((diff**2).mean()))
        mae  = float(np.abs(diff).mean())
        bias = float(diff.mean())
        corr = float(xr.corr(utrecht_masked, fao))

        metrics.append(dict(animal=animal, year=year,
                            rmse=rmse, mae=mae, bias=bias, correlation=corr))

        # ─ scatter
        plt.figure(figsize=(7,6))
        plt.scatter(fao.values.ravel(), utrecht_masked.values.ravel(),
                    s=5, alpha=0.35)
        one = np.linspace(0, np.nanmax(fao), 100)
        plt.plot(one, one, "r--", lw=1)
        plt.xlabel("FAO density"); plt.ylabel("Utrecht density")
        plt.title(f"{animal.capitalize()} {year} scatter")
        plt.tight_layout()
        plt.savefig(f"{PLOT_DIR}/scatter_{animal}_{year}.png")
        plt.close()

        # ─ diff map
        plt.figure(figsize=(9,4.5))
        diff.plot(cmap="RdBu",
                  vmin=-np.nanmax(np.abs(diff)),
                  vmax= np.nanmax(np.abs(diff)),
                  robust=True)
        plt.title(f"{animal.capitalize()} {year} (Utrecht – FAO)")
        plt.tight_layout()
        plt.savefig(f"{PLOT_DIR}/diff_map_{animal}_{year}.png")
        plt.close()

        print(f"    ✔ RMSE={rmse:.4f}, MAE={mae:.4f}, "
              f"Bias={bias:.4f}, r={corr:.3f}")

# ─── 3. WRITE SUMMARY ───────────────────────────────────────────────────
pd.DataFrame(metrics).to_csv("validation_summary.csv", index=False)
print("\n📄  Metrics saved → validation_summary.csv")

