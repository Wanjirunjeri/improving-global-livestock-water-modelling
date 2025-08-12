#!/usr/bin/env python3
"""
Build bar graphs from validation_summary_{year}.csv,
recomputing the overall total from species rows only (no ALL-LU).

Outputs go next to each CSV in $VSC_SCRATCH/fao_validation/plots{year}/
"""
import os, argparse, numpy as np, pandas as pd, matplotlib.pyplot as plt

ROOT = os.path.join(os.environ.get("VSC_SCRATCH", "/scratch/brussel/111/vsc11128"), "fao_validation")
ORDER8 = ["buffalo","cattle","chicken","duck","goat","horse","pig","sheep"]
ORDER6 = ["buffalo","cattle","chicken","goat","pig","sheep"]

def _has(df, col): return col in df.columns and df[col].notna().any()
def _order(df):
    present = [a for a in df["animal"].tolist()]
    base = ORDER8 if any(x in present for x in ("duck","horse")) else ORDER6
    out = [a for a in base if a in present]
    # keep any extras at end (e.g., “total6” if left in by mistake)
    out += [a for a in present if a not in out]
    return out

def _recomputed_total_row(df, year):
    # drop any preexisting total rows, then sum species present
    df_species = df[~df["animal"].str.startswith("total")]
    species_list = ORDER6 if year == 2020 else _order(df_species)
    species_list = [a for a in species_list if a in set(df_species["animal"])]
    if not species_list: return None
    sub = df_species.set_index("animal").loc[species_list]
    ut_sum = float(sub["utrecht_total"].sum()) if _has(sub, "utrecht_total") else np.nan
    fa_sum = float(sub["fao_total"].sum())     if _has(sub, "fao_total")     else np.nan
    n_sum  = int(sub["n_valid_points"].sum())  if _has(sub, "n_valid_points") else 0
    # compute % diff vs FAO for the grand totals
    diff  = fa_sum - ut_sum if np.isfinite(fa_sum) and np.isfinite(ut_sum) else np.nan
    pct   = (100.0*diff/fa_sum) if (np.isfinite(diff) and fa_sum not in (0, np.nan)) else np.nan
    return pd.Series({
        "animal": "total6" if year == 2020 else "total",
        "utrecht_total": ut_sum, "fao_total": fa_sum,
        "n_valid_points": n_sum, "total_diff_fao_minus_utrecht": diff,
        "total_diff_pct_of_fao": pct
    })

def _bar(df, col, outpng, title, ylabel, yzero=False, log_auto=False):
    if col not in df.columns or df[col].isna().all(): 
        print(f"[SKIP] {col} missing/empty"); return
    vals = df[col].astype(float).to_numpy()
    plt.figure(figsize=(max(8,1.2*len(df)), 4.6), dpi=180)
    if log_auto:
        pos = vals[np.isfinite(vals) & (vals>0)]
        if pos.size and (pos.max()/max(pos.min(),1e-12) > 100):
            plt.yscale("log")
    x = np.arange(len(df))
    plt.bar(x, vals)
    plt.xticks(x, [a.capitalize() for a in df["animal"]], rotation=45, ha="right")
    plt.ylabel(ylabel); plt.title(title); 
    if yzero: plt.axhline(0, color="k", lw=0.8)
    plt.grid(axis="y", alpha=0.3); plt.tight_layout()
    plt.savefig(outpng, bbox_inches="tight"); plt.close(); print("Saved:", outpng)

def _group_totals(df, outpng, title, millions=False):
    if not (_has(df, "utrecht_total") and _has(df, "fao_total")):
        print("[SKIP] totals columns missing"); return
    u = df["utrecht_total"].astype(float).to_numpy()
    f = df["fao_total"].astype(float).to_numpy()
    label = "Global total (count)"
    if millions:
        u, f = u/1e6, f/1e6
        label = "Global total (millions)"
    x = np.arange(len(df)); w = 0.4
    plt.figure(figsize=(max(8,1.2*len(df)), 4.6), dpi=180)
    plt.bar(x-w/2, u, width=w, label="Utrecht")
    plt.bar(x+w/2, f, width=w, label="FAO")
    plt.xticks(x, [a.capitalize() for a in df["animal"]], rotation=45, ha="right")
    plt.ylabel(label); plt.title(title); plt.grid(axis="y", alpha=0.3); plt.legend()
    plt.tight_layout(); plt.savefig(outpng, bbox_inches="tight"); plt.close(); print("Saved:", outpng)


def process_year(year, root):
    d = os.path.join(root, f"plots{year}")
    csv = os.path.join(d, f"validation_summary_{year}.csv")
   
    if not os.path.exists(csv):
        print(f"[WARN] Missing CSV for {year}: {csv}"); return
    df = pd.read_csv(csv)
    if "animal" not in df.columns:
        print(f"[WARN] No 'animal' col in {csv}"); return
    df["animal"] = df["animal"].astype(str).str.lower()

    # drop any preexisting total rows; we’ll add a recomputed one
    df = df[~df["animal"].str.startswith("total")].copy()

    # keep only useful numeric cols
    for c in ["utrecht_total","fao_total","n_valid_points","rmse","pearson_r",
              "mean_bias_fao_minus_utrecht","mae","median_abs_error",
              "total_diff_fao_minus_utrecht","total_diff_pct_of_fao",
              "slope_fao_vs_utrecht","intercept_fao_vs_utrecht"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")

    # **Add recomputed total row from species in CSV**
    tot = _recomputed_total_row(df, year)
    if tot is not None:
        df = pd.concat([pd.DataFrame([tot]), df], ignore_index=True)

    # order categories nicely
    order = _order(df[df["animal"]!="total6"]) if year!=2020 else ORDER6
    order = (["total6"] if year==2020 else ["total"]) + [a for a in order if a in set(df["animal"])]
    df = df.set_index("animal").reindex(order).reset_index()

    # plots
    _bar(df, "pearson_r", os.path.join(d, f"bars_pearson_r_{year}.png"),
         f"Pearson r by animal ({year})", "r (−1..1)")
    _bar(df, "rmse", os.path.join(d, f"bars_rmse_{year}.png"),
         f"RMSE by animal ({year})", "RMSE", log_auto=True)
    _bar(df, "mean_bias_fao_minus_utrecht", os.path.join(d, f"bars_mean_bias_{year}.png"),
         f"Mean bias (FAO − Utrecht) by animal ({year})", "Bias (count/cell)", yzero=True)
    _bar(df, "mae", os.path.join(d, f"bars_mae_{year}.png"),
         f"MAE by animal ({year})", "MAE (count/cell)", log_auto=True)
    _bar(df, "median_abs_error", os.path.join(d, f"bars_median_abs_error_{year}.png"),
         f"Median Abs Error by animal ({year})", "Median |error| (count/cell)")
    _bar(df, "total_diff_pct_of_fao", os.path.join(d, f"bars_pctdiff_vs_fao_{year}.png"),
         f"% difference vs FAO by animal ({year})", "% (FAO − Utrecht)/FAO × 100", yzero=True)
    _bar(df, "n_valid_points", os.path.join(d, f"bars_npoints_{year}.png"),
         f"N valid points by animal ({year})", "N cells")

    # **totals side-by-side** (uses recomputed total row)
    _group_totals(df, os.path.join(d, f"bars_totals_side_by_side_{year}_recomputed.png"),
                  f"Global totals by animal ({year}) — recomputed from species")
    _group_totals(df, os.path.join(d, f"bars_totals_side_by_side_millions_{year}_recomputed.png"),
                  f"Global totals by animal ({year}) — recomputed from species", millions=True)

    print(f"[{year}] done → {d}")


def main():
    default_root = os.path.join(
        os.environ.get("VSC_SCRATCH", "/scratch/brussel/111/vsc11128"),
        "fao_validation"
    )
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--root", default=default_root)
    args = ap.parse_args()

    for y in args.years:
        process_year(y, args.root)


if __name__ == "__main__":
    main()

