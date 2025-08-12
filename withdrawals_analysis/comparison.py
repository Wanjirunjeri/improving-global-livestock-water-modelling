import xarray as xr
import matplotlib.pyplot as plt

# File paths (update as needed)
year=2015
generated_path = f"/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid/Liv_WD_{year}.nc"
harmonized_path = f"/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock/withdrawal_livestock_m3_per_day_spatially_harmonized_using_Khan_et_al2023_weights_{year}.nc"

# Load datasets
gen_ds = xr.open_dataset(generated_path)
harmo_ds = xr.open_dataset(harmonized_path)

# 1. Generated dataset: sum over time (already m³/day), get annual total
gen_annual = gen_ds.sum(dim="time")
gen_total = sum([gen_annual[v] for v in gen_annual.data_vars if v.endswith("_wd")])

# 2. Harmonized dataset: convert m³/s to m³/month, then sum for year
harmo_var = list(harmo_ds.data_vars)[0]
days_in_month = harmo_ds["time"].dt.days_in_month
harmo_monthly_total = harmo_ds[harmo_var] * days_in_month * 86400  # m³/s × sec/month
harmo_annual_total = harmo_monthly_total.sum(dim="time")  # now in m³/cell/year

# 3. Compute difference (generated - harmonized)
diff = gen_total - harmo_annual_total

# 4. Plot difference map
plt.figure(figsize=(10, 5))
diff.plot(cmap="bwr", robust=True, cbar_kwargs={"label": "Generated - Harmonized (m³/cell/year)"})
plt.title(f"Difference in Annual Livestock Withdrawal {year}\n(Generated - Harmonized)")
plt.tight_layout()
plt.savefig(f"difference_map_{year}.png", dpi=300)

