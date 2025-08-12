#!/usr/bin/env python3
"""
Batch driver to *generate & save* maps plus country‑level time‑series
using the helper functions already defined in `livestock_water_analysis.py`.

----------------------------------------------------------
Quick start (on the VUB‑HPC login node)
----------------------------------------------------------
module load 2023
module load Python/3.10.4
python batch_generate_plots.py \
       --years 2000 2005 2010 2015 2019 \
       --countries USA IND BRA ETH MNG \
       --figdir   /scratch/brussel/111/vsc11128/figs

What it does
------------
* Loops over the *years* list and writes `map_<year>.png` for each
  (Robinson projection, km³ yr⁻¹ scale).
* Loops over the *ISO‑3* codes in *countries* and writes
  `<ISO>_timeseries.png` (annual totals 1980‑2019 with LOESS smoother).

Adjust the year range, ISO list, or figure directory with CLI flags.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from livestock_water_analysis import (
    load_generated,
    load_harmonised,
    plot_global_map,
    plot_country_timeseries,
)

# ----------------------------------------------------------------------------
# Command‑line parsing
# ----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Batch renderer for livestock‑withdrawal plots",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(range(1980, 2020)),
        help="One or more years (1971‑2019) for which to draw global maps",
    )
    p.add_argument(
        "--countries",
        nargs="+",
        default=["USA", "IND"],
        help="ISO‑3 codes to plot annual time‑series (1980‑2019)",
    )
    p.add_argument(
        "--figdir",
        type=Path,
        default=Path("./figs"),
        help="Output directory for PNGs (will be created if absent)",
    )
    return p.parse_args()

# ----------------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------------

def main(years: List[int], countries: List[str], figdir: Path):
    figdir.mkdir(parents=True, exist_ok=True)

    # 1. Global maps ----------------------------------------------------------
    for y in years:
        if y >= 1980:
            ds = load_generated(y)
        else:
            ds = load_harmonised(y)
        outfile = figdir / f"map_{y}.png"
        print(f"[MAP ] {y} → {outfile}")
        plot_global_map(ds, y, out=outfile)

    # 2. Country time‑series (annual totals) ----------------------------------
    yrs = list(range(1980, 2020))  # fixed 1980‑2019 span as per regrid set
    for iso in countries:
        outfile = figdir / f"{iso}_timeseries.png"
        print(f"[TS  ] {iso} 1980‑2019 → {outfile}")
        plot_country_timeseries(iso.upper(), yrs, out=outfile)


if __name__ == "__main__":
    ns = parse_args()
    main(ns.years, ns.countries, ns.figdir)

