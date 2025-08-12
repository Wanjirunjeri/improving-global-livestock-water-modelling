#!/usr/bin/env python3
"""
global_totals_line.py
~~~~~~~~~~~~~~~~~~~~~
Iterate through **both** datasets file-by-file, compute global annual totals,
and export a dual-colour line graph.

Usage
-----
python global_totals_line.py \
       /scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock \
       /scratch/brussel/111/vsc11128/liv_wd_yearly_regrid \
       /scratch/brussel/111/vsc11128/liv_wd_yearly/analysis/global_totals.png
"""
from __future__ import annotations

import calendar
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

ANIMALS = [
    "cattle", "buffalo", "goats", "sheep",
    "pig", "chicken", "ducks", "horses",
]

# ----------------------------------------------------------------------------- 
# Helpers
# ----------------------------------------------------------------------------- 

START_YEAR = 1970
END_YEAR   = 2020

def secs_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1] * 86_400


def harmonised_totals(harm_dir: Path):
    years, vals = [], []
    for fp in sorted(harm_dir.glob("withdrawal_*_????.nc")):
        m = re.search(r"(\d{4})\.nc$", fp.name)
        if not m:
            continue
        year = int(m.group(1))
        ds = xr.open_dataset(fp, decode_times=False)
        secs = [secs_in_month(year, mm) for mm in range(1, 13)]
        factor = xr.DataArray(secs, dims="time")

        # -------------- HARMONIZED: monthly km³ ----------------
        # pick the variable robustly
        harm_var_candidates = ["withd_liv", "total_withdrawal_livestock"]
        harm_var = None
        for v in harm_var_candidates:
            if v in ds.data_vars:
                harm_var = v
                break
        if harm_var is None:
            raise ValueError(f"None of {harm_var_candidates} found in harmonized dataset")

        year_m3 = (ds[harm_var] * factor).sum()
        vals.append(year_m3.item() / 1e9)   # km³
        years.append(year)
        ds.close()
    return np.array(years), np.array(vals)


def generated_totals(gen_dir: Path):
    years, vals = [], []
    for fp in sorted(gen_dir.glob("Liv_WD_????.nc")):
        m = re.search(r"(\d{4})\.nc$", fp.name)
        if not m:
            continue
        year = int(m.group(1))
        ds = xr.open_dataset(fp, decode_times=False)
        total = sum(ds[f"{a}_wd"] for a in ANIMALS)
        vals.append(total.sum().item() / 1e9)  # km³
        years.append(year)
        ds.close()
    return np.array(years), np.array(vals)


def align_to_axis(years: np.ndarray, vals: np.ndarray, axis_years: np.ndarray) -> np.ndarray:
    """Return an array aligned to axis_years, with NaN where data is missing."""
    out = np.full(axis_years.shape, np.nan, dtype=float)
    idx = {y: i for i, y in enumerate(axis_years)}
    for y, v in zip(years, vals):
        if y in idx:
            out[idx[y]] = v
    return out

# ----------------------------------------------------------------------------- 
# Main
# ----------------------------------------------------------------------------- 

def main(harm_path: str, gen_path: str, fig_path: str):
    h_years, h_vals = harmonised_totals(Path(harm_path))   # starts 1971
    g_years, g_vals = generated_totals(Path(gen_path))     # starts 1980

    # Common year axis spanning BOTH datasets
    ymin = int(min(h_years.min(), g_years.min()))
    ymax = int(max(h_years.max(), g_years.max()))
    #years_axis = np.arange(ymin, ymax + 1)

    # Common year axis fixed to full range (1970–2020)
    years_axis = np.arange(START_YEAR, END_YEAR + 1)

    # Align each series to the common axis (NaN where no data)
    h_aligned = align_to_axis(h_years, h_vals, years_axis)
    g_aligned = align_to_axis(g_years, g_vals, years_axis)


    # Align each series to the common axis (NaN for missing early years)
    #h_aligned = align_to_axis(h_years, h_vals, years_axis)
    #g_aligned = align_to_axis(g_years, g_vals, years_axis)
    
    """
    plt.figure(figsize=(7.5, 4.8))
    plt.plot(years_axis, h_aligned, label="Harmonised", lw=1.8)
    plt.plot(years_axis, g_aligned, label="Generated", lw=1.8)
    plt.xlim(START_YEAR, END_YEAR)
    plt.ylabel("Global withdrawal (km³ yr⁻¹)")
    plt.xlabel("Year")
    plt.grid(ls="--", lw=0.4, alpha=0.8)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300)
    print(f"Figure written → {fig_path}")
    """
    plt.figure(figsize=(7.5, 4.8))
    plt.plot(years_axis, h_aligned, label="Harmonised", lw=1.8)
    plt.plot(years_axis, g_aligned, label="Generated", lw=1.8)
    plt.xlim(START_YEAR, END_YEAR)
    plt.xticks(np.arange(START_YEAR, END_YEAR + 1, 5))  # every 5 years (optional)
    plt.title("Annual Global Livestock Drinking Water Withdrawal")
    plt.ylabel("Global withdrawal (km³ yr⁻¹)")
    plt.xlabel("Year")
    plt.grid(ls="--", lw=0.4, alpha=0.8)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python global_totals_line.py <harm_dir> <gen_dir> <out_png>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])

