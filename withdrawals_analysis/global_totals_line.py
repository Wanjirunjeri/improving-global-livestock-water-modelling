#!/usr/bin/env python3
"""
global_totals_line.py
~~~~~~~~~~~~~~~~~~~~~
Iterate through **both** datasets file‑by‑file, compute global annual totals,
and export a dual‑colour line graph.

Usage
-----
```bash
python global_totals_line.py \
       /scratch/brussel/111/vsc11128/liv_wd_yearly/Sabin/livestock \
       /scratch/brussel/111/vsc11128/liv_wd_yearly_regrid \
       /scratch/brussel/111/vsc11128/liv_wd_yearly/analysis/global_totals.png
```
"""
from __future__ import annotations

import calendar
import glob
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

def secs_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1] * 86_400


def harmonised_totals(harm_dir: Path):
    years, vals = [], []
    for fp in sorted(harm_dir.glob("withdrawal_*_????.nc")):
        year = int(re.search(r"(\d{4})\.nc$", fp.name)[0])
        ds = xr.open_dataset(fp, decode_times=False)
        secs = [secs_in_month(year, m) for m in range(1, 13)]
        factor = xr.DataArray(secs, dims="time")
        year_m3 = (ds["withd_liv"] * factor).sum()
        vals.append(year_m3.item() / 1e9)   # km³
        years.append(year)
    return np.array(years), np.array(vals)


def generated_totals(gen_dir: Path):
    years, vals = [], []
    for fp in sorted(gen_dir.glob("Liv_WD_????.nc")):
        year = int(re.search(r"(\d{4})\.nc$", fp.name)[0])
        ds = xr.open_dataset(fp, decode_times=False)
        total = sum(ds[f"{a}_wd"] for a in ANIMALS).sum()
        vals.append(total.item() / 1e9)     # km³
        years.append(year)
    return np.array(years), np.array(vals)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main(harm_path: str, gen_path: str, fig_path: str):
    h_years, h_vals = harmonised_totals(Path(harm_path))
    g_years, g_vals = generated_totals(Path(gen_path))

    plt.figure(figsize=(6.5, 4))
    plt.plot(h_years, h_vals, label="Harmonised", lw=1.8)
    plt.plot(g_years, g_vals, label="Liv_WD", lw=1.8)
    plt.ylabel("Global withdrawal (km³ yr⁻¹)")
    plt.xlabel("Year")
    plt.grid(ls="--", lw=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300)
    print(f"Figure written → {fig_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python global_totals_line.py <harm_dir> <gen_dir> <out_png>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])

