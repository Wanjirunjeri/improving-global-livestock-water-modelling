
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import re
from glob import glob


path = r"/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock/withdrawal_*.nc"  # adjust pattern
files = sorted(glob(path))

records = []
for f in files:
    year = int(re.search(r'_(\d{4})\.nc$', f).group(1))
    ds = xr.open_dataset(f, chunks={"time": 90})          # lazy load
    var = list(ds.data_vars)[0] # or put exact name, e.g. 'total_wd'

    monthly = (
        ds[var]
        .resample(time='MS'))

    time_index = ds['time'].to_index()
    days_in_month = time_index.days_in_month
    days_in_month_da = xr.DataArray(days_in_month.values, coords=[ds['time']], dims=["time"])
    monthly_m3 = ds["withd_liv"] * days_in_month_da*86400
    monthly_m3.name = "withdrawal_m3_per_month"

    
    # m³/day -> m³/year: sum over time; then global sum over lat/lon
    total_m3 = ds['withdrawal_m3_per_month'].sum(dim=["time", "lat", "lon"]).compute()
    records.append((year, float(total_m3) / 1e9))          # km³

df = pd.DataFrame(records, columns=["year", "km3"])
print (df.columns)
# Plot
plt.figure(figsize=(8,4))
plt.plot(df.year, df.km3, marker="o")
plt.ylabel("Global livestock withdrawal (km³/year)")
plt.xlabel("Year")
plt.title("1971–1980 Global Livestock Water Withdrawals")
plt.grid(True)
plt.tight_layout()
plt.Savefig("1971–2019 Global Livestock Water Withdrawals")

