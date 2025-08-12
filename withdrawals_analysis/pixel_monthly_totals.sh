import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import pandas as pd
import os
import numpy as np


plt.rcParams.update({
    "axes.titlesize": 18,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
})



historical_dir="/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock"
future_harmonized_dir="/scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/future"


year=2015
outdir= f"/scratch/brussel/111/vsc11128/liv_wd_yearly/analysis/plots4_{year}"
os.makedirs(outdir, exist_ok=True)

# 1. Load the dataset
ds = xr.open_dataset(f"/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid/Liv_WD_{year}.nc")
#Load dataset 2
if 1980 <= year < 2020:
        filename = f"withdrawal_livestock_m3_per_day_spatially_harmonized_using_Khan_et_al2023_weights_{year}.nc"
        filepath =os.path.join(historical_dir,filename)
else:
	raise FileNotFoundError(f"No file found for year {year}")


try:
	harmo_ds = xr.open_dataset(filepath)
except Exception as e:
	raise RuntimeError(f"Could not open harmonized dataset: {filepath}\n{e}")


# 2. Define target point
target_lat =20.5937 #46.8625 #20.5937 #-3.4653 #46.8625 # 9.145  37.0902 # Example: Nairobi
target_lon =78.9629 #103.8467  #78.9629 #-62.2159 #103.8467  #40.4897 -95.7129

# List of animal types to include
vars_to_sum = [var for var in ds.data_vars if var.endswith('_wd')]


# Sum withdrawal at the nearest pixel
point_sum = sum(
    ds[var].sel(lat=target_lat, lon=target_lon, method='nearest') for var in vars_to_sum
)

# Decode time
try:
    ds = xr.decode_cf(ds)
except Exception:
    pass
point_sum['time'] = ds['time']

# Resample to monthly totals
monthly_tot = point_sum.resample(time='MS').sum()
monthly_total = monthly_tot / 1e9

# 🔥 4. Assign name AFTER resampling
monthly_total.name = "withdrawal_km3_per_month"

# Convert to pandas for easier control of labels
monthly_df = monthly_total.to_dataframe().reset_index()
monthly_df['month'] = monthly_df['time'].dt.strftime('%b')
monthly_df['month_num'] = monthly_df['time'].dt.month

"""
min_val = 0 #monthly_df["withdrawal_m3_per_month"].min()
max_val = harmo_monthly_m3.max().item()   #monthly_df["withdrawal_m3_per_month"].max()

monthly_df["normalized"] = (
    (monthly_df["withdrawal_m3_per_month"] - min_val) / (max_val - min_val)
)

# Sort to ensure January–December order
monthly_df = monthly_df.sort_values('month_num')
"""
#-----------------------------------------------------------------------
if 2010 < year <2019:
	harmo_point = harmo_ds["total_withdrawal_livestock"].sel(lat=target_lat, lon=target_lon, method="nearest")
else:
	harmo_point = harmo_ds["withd_liv"].sel(lat=target_lat, lon=target_lon, method="nearest")

	# Convert time to pandas for days-in-month lookup
time_index = harmo_point['time'].to_index()
days_in_month = time_index.days_in_month

# Create a matching DataArray
days_in_month_da = xr.DataArray(days_in_month.values, coords=[harmo_point['time']], dims=["time"])

# Multiply daily values by days in month to get m³/month
harmo_monthly_m3 = harmo_point * days_in_month_da*86400
harmo_monthly_km3 = harmo_monthly_m3 / 1e9
harmo_monthly_km3.name = "harmo_withdrawal_km3_per_month"
# Compute min and max
min_val = 0   #harmo_monthly_m3.min().item()
max_val = max(harmo_monthly_km3.max().item(), monthly_df["withdrawal_km3_per_month"].max())    # harmo_monthly_m3.max().item()

# Normalize
harmo_normalized = (harmo_monthly_km3 - min_val) / (max_val - min_val)
harmo_normalized.name = "harmo_normalized"

df = harmo_monthly_km3.to_dataframe().reset_index()
df["normalized"] = harmo_normalized.values
df["month"] = df["time"].dt.strftime("%b")
df["month_num"] = df["time"].dt.month
df = df.sort_values("month_num")


monthly_df["normalized"] = (
    (monthly_df["withdrawal_km3_per_month"] - min_val) / (max_val - min_val)
)
monthly_df = monthly_df.sort_values('month_num')


# Plot as bar chart
plt.figure(figsize=(10, 5))

plt.bar(
    monthly_df["month"], 
    monthly_df["withdrawal_km3_per_month"],
    width=0.6, 
    label="Liv_WD", 
    alpha=0.4,
    color="tab:green"
)

plt.bar(
    df["month"], 
    df["harmo_withdrawal_km3_per_month"], 
    label="Harmonized",
    width=0.4,
    alpha=0.6,
    color="tab:red"
)

# ──── scientific y-axis: ×10⁻⁴ ───────────────────────────────
ax = plt.gca()                                           # current Axes
fmt = ScalarFormatter(useMathText=True)                  # 1×10⁻⁴, not 1e-04
fmt.set_scientific(True)
fmt.set_powerlimits((-5, -5))                            # force exponent −4
fmt.set_useOffset(False)                                 # no overall offset
ax.yaxis.set_major_formatter(fmt)
ax.yaxis.get_offset_text().set_fontsize(10)              # tidy the tiny “×10⁻⁴”
ax.yaxis.get_offset_text().set_va("bottom")              # align nicely
# ────────────────────────────────────────────────────────────

plt.title(f"Monthly Withdrawal Comparison at ({target_lat}, {target_lon}) - {year}")
plt.ylabel("Withdrawal (km³/month)")
plt.xlabel("Month")
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(outdir, f"comparison_total_km3_{target_lat}_{target_lon}_{year}.png"), dpi=300)
plt.close()


#--------------------------second bar plot-----------------------------
plt.figure(figsize=(10, 5))

plt.bar(
    monthly_df["month"], 
    monthly_df["normalized"],
    width=0.6, 
    label="Liv_WD", 
    alpha=0.4,
    color="tab:green"
)

plt.bar(
    df["month"], 
    df["normalized"],
    width=0.4, 
    label="Harmonized", 
    alpha=0.6,
    color="tab:red"
)

plt.title(f"Scaled Monthly Withdrawal Comparison at ({target_lat}, {target_lon}) - {year}")
plt.ylabel("Scaled Value (0–1)")
plt.xlabel("Month")
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(outdir, f"comparison_normalized_{target_lat}_{target_lon}_{year}.png"), dpi=300)
plt.close()

"""
fig, ax1 = plt.subplots(figsize=(10, 5))

x = np.arange(len(monthly_df["month"]))

ax1.bar(x, monthly_df["withdrawal_m3_per_month"], width=0.6, label="Liv_WD", color="tab:green", alpha=0.6)
ax2 = ax1.twinx()
ax2.bar(x, df["harmo_withdrawal_m3_per_month"], width=0.4, label="Harmonized", color="tab:red", alpha=0.6)

plt.xticks(x, monthly_df["month"])
ax1.set_ylabel("Liv_WD (m³/month)")
ax2.set_ylabel("Harmonized (m³/month)")

plt.title(f"Monthly Withdrawal Comparison at ({target_lat}, {target_lon}) - {year}")
fig.tight_layout()
plt.savefig(os.path.join(outdir, f"comparison_dual_axis_{target_lat}_{target_lon}_{year}.png"), dpi=300)
plt.close()
"""



"""
# Compute mean values
mean_liv = monthly_df["withdrawal_km3_per_month"].mean()
mean_harmo = df["harmo_withdrawal_km3_per_month"].mean()

# Compute the offset needed
mean_shift = mean_liv - mean_harmo

# Create shifted harmonized values
df["harmo_shifted"] = df["harmo_withdrawal_m3_per_month"] + mean_shift

x = np.arange(len(monthly_df["month"]))
width = 0.6

plt.figure(figsize=(10, 5))

# Plot Liv_WD
plt.bar(x, monthly_df["withdrawal_m3_per_month"], width=0.4, label="Liv_WD", alpha=0.4, 
	color="tab:green", edgecolor="none")

# Plot shifted harmonized
plt.bar(x, df["harmo_shifted"], width=0.6, label="Harmonized (shifted)", alpha=0.6, 
	color="tab:red",edgecolor="none", zorder=2)

plt.xticks(x, monthly_df["month"])
plt.title(f"Comparison of Monthly Withdrawals (Shifted) at ({target_lat}, {target_lon}) - {year}")
plt.ylabel("Withdrawal (m³/month)")
plt.xlabel("Month")
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(outdir, f"comparison_shifted_m3_({target_lat},{target_lon})_{year}.png"), dpi=300)
plt.close()
"""

"""
plt.figure(figsize=(10, 5))


plt.bar(monthly_df['month'], monthly_df[monthly_total.name],
	label="Livestock water requirements", alpha=0.6)
plt.title(f"Monthly Livestock Withdrawal at ({target_lat}, {target_lon}) - 1980")
plt.ylabel("Total withdrawal (m³/month)")
plt.xlabel("Month")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(f"monthly_bar_withdrawal_{target_lat}_{target_lon}.png", dpi=300)
plt.close()




plt.bar(monthly_df['month'], monthly_df["normalized"])
plt.title(f"Normalized Monthly Livestock Withdrawal (0–1) at ({target_lat}, {target_lon})-1988 ")
plt.ylabel("Normalized Value")
plt.xlabel("Month")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(f"monthly_bar_normalized_{target_lat}_{target_lon}.png", dpi=300)
plt.close()
"""
