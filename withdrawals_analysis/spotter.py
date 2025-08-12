# livestock_bluered.py
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Circle
from matplotlib.ticker import ScalarFormatter
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import os
import regionmask

# ------------- USER INPUTS -------------
year=2015
nc_path   = f"/scratch/brussel/111/vsc11128/liv_wd_yearly_regrid/Liv_WD_{year}.nc"     # NetCDF file
point_lat =20.5937 #46.8625 #37.0902 #20.5937  #-3.4653   #46.8625   #9.145 #37.0902     #  degrees north  (update!)
point_lon =78.9629 #103.8467 #-95.7129 #78.9629   #-62.2159 #103.8467   #40.4897 # -95.7129     #  degrees east   (update!)
dpi       = 200
outdir=f"/scratch/brussel/111/vsc11128/liv_wd_yearly/analysis/plots4_{year}"

# ---------------------------------------
plt.rcParams.update({
    "axes.titlesize": 18,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
})




# --- A blue→white→red palette (close to ncview “Bluered”) ---
cmap = plt.get_cmap("viridis")
   
    
os.makedirs(outdir,exist_ok=True)

def read_and_sum(nc_path: Path):
    """Return the sum of all *_wd variables as a DataArray (lat, lon)."""
    ds = xr.open_dataset(nc_path)

    livestock_vars = [v for v in ds.data_vars if v.endswith("_wd")]
    if not livestock_vars:
        raise ValueError("No variables ending with '_wd' were found.")
    # stack species into a new dimension then sum
    arr = xr.concat([ds[v] for v in livestock_vars], dim="variable").sum("variable", skipna=True)

    # sum over daily slices → annual total
    if "time" in arr.dims:
        arr = arr.sum("time", skipna=True)
    
    arr = arr/1e9
    # ------------------------------------------------------------------
    try:                                     # newer (>= 0.11.0)
        land = regionmask.defined_regions.natural_earth_v5_0_0.land_110
    except AttributeError:                   # older (0.9 – 0.10)
        land = regionmask.defined_regions.natural_earth_v4_1_0.land_110

    land_mask = land.mask(arr)                           # NaN over ocean, 0 over land
    arr = arr.where(~np.isnan(land_mask))                # keep only land cells

    return arr  # dims: (lat, lon)
"""
    # 1️⃣ stack livestock vars into new 'variable' axis
    arr = xr.concat([ds[v] for v in livestock_vars], dim="variable")
    arr = arr.assign_coords(variable=livestock_vars)

    # 2️⃣ combine the species
    arr = arr.sum(dim="variable", skipna=True)

    # 3️⃣ NEW: remove the time axis (choose the reduction you prefer)
    if "time" in arr.dims:
        arr = arr.sum(dim="time", skipna=True)      # <-- annual total
        # arr = arr.mean(dim="time", skipna=True)   # <-- daily mean
        # arr = arr.isel(time=0, drop=True)         # <-- first day only
    
    return arr   # now 2‑D (lat, lon)




    # 1️⃣ Convert to a DataArray so we get the new 'variable' dimension
    arr = ds[livestock_vars].to_array(dim="variable")   # ➜ DataArray

    # 2️⃣ Optionally drop a singleton time dimension
    if "time" in arr.dims and arr.sizes["time"] == 1:
        arr = arr.isel(time=0, drop=True)

    # 3️⃣ Sum over the livestock species
    summed = arr.sum(dim="variable", skipna=True)

    return summed          # dims: (lat, lon)
"""



def plot_total(arr, lat_pt, lon_pt):
    """Plot the field with a star on the chosen point and annotate its value."""
    proj = ccrs.PlateCarree()
    fig  = plt.figure(figsize=(10, 5), dpi=dpi)
    ax   = fig.add_subplot(1, 1, 1, projection=proj)

    # Use symmetric color‑limits around zero to exploit blue↔red meaningfully
    vmax = np.nanpercentile(np.abs(arr), 99)   # robust upper bound
    vmin =0

    mesh = ax.pcolormesh(
        arr.lon, arr.lat, arr,
        cmap=cmap, vmin=vmin, vmax=vmax,
        transform=proj, shading="auto"
    )
    cbar = fig.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.05)
    cbar.set_label("Livestock water requirement (km³ cell⁻¹)")


    ax.add_feature(cfeature.COASTLINE, linewidth=0.4)
    ax.add_feature(cfeature.BORDERS,   linewidth=0.2)
    ax.set_global()
    ax.set_title(f"Total Livestock Drinking‑Water requirement for {year}")

    # ---------- red vignette marker ----------
    ax.scatter(
        lon_pt, lat_pt,
        s=30, color="red", edgecolors="white", linewidths=0.4,
        transform=proj, zorder=5
    )
    for r, alpha in [(0.4, 0.25), (0.2, 0.4)]:  # ° and transparency
        circ = Circle(
            (lon_pt, lat_pt), radius=r,
            transform=proj, facecolor="red", edgecolor="none",
            alpha=alpha, zorder=5
        )
        ax.add_patch(circ)
    # -----------------------------------------
    out = Path(outdir)/f"livestock_{point_lat},{point_lon}_{year}.png"
    fig.savefig(out, bbox_inches="tight", dpi=dpi)
    plt.show()
    print(f"Figure saved → {out.resolve()}")

def main():
    total = read_and_sum(nc_path)
    plot_total(total, point_lat, point_lon)

if __name__ == "__main__":
    main()

