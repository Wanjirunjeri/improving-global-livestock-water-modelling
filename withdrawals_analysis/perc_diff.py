import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

# -------- CONFIG --------
year = 1984
generated_path  = f"/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid/Liv_WD_{year}.nc"
harmonized_path = f"/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock/withdrawal_livestock_m3_per_day_spatially_harmonized_using_Khan_et_al2023_weights_{year}.nc"

# -------- LOAD --------
gen_ds   = xr.open_dataset(generated_path)
harmo_ds = xr.open_dataset(harmonized_path)

# -------- ANNUAL TOTALS PER CELL --------
# Generated: m3/cell/day → m3/cell/year (sum over days), then sum species
gen_annual = gen_ds.sum(dim="time")
gen_total  = sum([gen_annual[v] for v in gen_annual.data_vars if v.endswith("_wd")])

# Harmonized: monthly mean m3/s → m3/month (× days_in_month × 86400) → m3/year
harmo_var = list(harmo_ds.data_vars)[0]
days_in_month = harmo_ds["time"].dt.days_in_month
harmo_monthly_total = harmo_ds[harmo_var] * days_in_month * 86400.0
harmo_annual_total  = harmo_monthly_total.sum(dim="time")

# -------- PERCENT DIFFERENCE --------
# %diff = 100 * (Harmonized - Generated) / Harmonized
denom = gen_total.where(harmo_annual_total > 0)  # avoid div-by-zero
pct_diff = 100.0 * (gen_total- harmo_annual_total) / denom

# Make a symmetric color scale around 0 using robust percentiles
abs_pct = np.abs(pct_diff.values)
finite_abs = abs_pct[np.isfinite(abs_pct)]
if finite_abs.size:
    lim = np.nanpercentile(finite_abs, 98)  # clip extreme outliers
    vmin, vmax = -lim, +lim
else:
    vmin, vmax = -100, 100

# -------- PLOT --------
plt.figure(figsize=(10, 5))
pct_diff.plot(
    cmap="RdBu_r", vmin=vmin, vmax=vmax,  # red = Harmonized > Generated; blue = Harmonized < Generated
    cbar_kwargs={"label": "Percent difference [%]\n(Generated−Harmonized) / Generated × 100"}
)
plt.title(f"Percent Difference in Annual Livestock Withdrawal ({year})")
plt.tight_layout()
plt.savefig(f"percent_difference_HminusG_{year}.png", dpi=300)
plt.show()

