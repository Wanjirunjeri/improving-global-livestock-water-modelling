#!/usr/bin/env python3
"""Livestock withdrawal factors vs temperature (15–35 °C)."""

from __future__ import annotations

from typing import Callable, Mapping

import os
import sys
import types

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb

# ──────────────────────────────────────────────────────────────────────────
# Optional dependency shim – keeps notebooks happy if ``micropip`` is absent
# ──────────────────────────────────────────────────────────────────────────
if "micropip" not in sys.modules:  # pragma: no cover
    micropip_stub = types.ModuleType("micropip")

    def _unsupported(*_args, **_kwargs):  # noqa: D401 – stub helper
        raise RuntimeError("micropip is unavailable in this environment")

    micropip_stub.install = _unsupported
    sys.modules["micropip"] = micropip_stub

# ──────────────────────────── 0. SOURCE DATA ─────────────────────────────
_WITHDRAWAL_DATA: dict[str, np.ndarray] = {
    "cattle":  np.array([102.8, 114.8, 126.8]),
    "goats":   np.array([7.6,   9.6,   11.9 ]),
    "sheep":   np.array([8.7,   12.9,  20.1 ]),
    "chicken": np.array([0.177, 0.331, 0.62 ]),
    "pig":     np.array([17.2,  28.3,  46.7 ]),
    "buffalo": np.array([56.2,  71.27, 85.23]),
    "horses":  np.array([31.81, 40.33, 48.6 ]),
    "ducks":   np.array([0.36,  0.7,   1.33 ]),
}

NumberArray = np.ndarray | float | int

# ────────────────────────── 1. FACTOR FUNCTIONS ──────────────────────────
def _make_factor_fn(y15: float, y35: float) -> Callable[[NumberArray], NumberArray]:
    """Return a linear f(temp) fixed at (15 °C, *y15*) and (35 °C, *y35*)."""
    slope = (y35 - y15) / 20.0  # °C span

    def _fn(temp: NumberArray) -> NumberArray:  # noqa: D401 – small helper
        return y15 + slope * (np.asarray(temp, dtype=float) - 15.0)

    _fn.__doc__ = (
        f"Linear withdrawal factor anchored at 15 °C ({y15:.2f} L) "
        f"and 35 °C ({y35:.2f} L)."
    )
    return _fn


FACTOR_FNS: Mapping[str, Callable[[NumberArray], NumberArray]] = {
    animal: _make_factor_fn(v[0], v[2]) for animal, v in _WITHDRAWAL_DATA.items()
}

# ─────────────────────────── 2.  PUBLIC API ──────────────────────────────
def withdrawal_factor(animal: str, temperature: NumberArray) -> NumberArray:
    """Litres /head /day for *animal* at *temperature* (°C).

    Temperatures are clipped to 15–35 °C before applying the
    species-specific linear model.
    """
    animal = animal.lower()
    if animal not in FACTOR_FNS:
        raise KeyError(f"Unknown animal '{animal}'. Choose from {list(FACTOR_FNS)}.")

    temp_clip = np.clip(temperature, 15.0, 35.0)
    return FACTOR_FNS[animal](temp_clip)


def withdrawal_by_gridcell(
    animal: str,
    temperature: xr.DataArray,
    density: xr.DataArray,
) -> xr.DataArray:
    """Litres per grid-cell per day (Utrecht style)."""

    def _vec(temp: NumberArray, *, animal: str) -> NumberArray:  # adapter
        return withdrawal_factor(animal, temp)

    factor = xr.apply_ufunc(
        _vec,
        temperature,
        kwargs={"animal": animal},
        vectorize=True,
        dask="parallelized",
        output_dtypes=[temperature.dtype],
    )
    return factor * density

# ─────────────────────────── 3.  DIAGNOSTIC PLOT ─────────────────────────
def plot_withdrawal_curves(temp_range: np.ndarray | None = None) -> None:
    """Plot dotted lines of withdrawal vs temperature for every animal."""
    if temp_range is None:
        temp_range = np.linspace(15, 35, 400)

    plt.figure(figsize=(8.5, 4))
    for animal, fn in FACTOR_FNS.items():
        plt.plot(temp_range, fn(temp_range), ":", label=animal)

    plt.xlabel("Temperature (°C)")
    plt.ylabel("Litres per head per day")
    plt.title("Livestock drinking water requirement vs temperature")
    
    # 2️⃣  legend outside the right border
    plt.legend(
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),        # x = 102 %, y = 50 %
        borderaxespad=0,
        fontsize="small",
        ncol=1,
    )

    plt.tight_layout(rect=[0, 0, 0.85, 1])  # leave space on the right


    # ensure ./plots exists
    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/my_result.png", dpi=300, bbox_inches="tight")
    plt.show()

# ─────────────────────────── 4. SELF-TESTS ───────────────────────────────
def _self_tests() -> None:  # pragma: no cover
    """Quick sanity checks."""
    for animal, v in _WITHDRAWAL_DATA.items():
        y15, _, y35 = v
        assert np.isclose(withdrawal_factor(animal, 15), y15)
        assert np.isclose(withdrawal_factor(animal, 35), y35)
        assert np.isclose(withdrawal_factor(animal, 10), y15)
        assert np.isclose(withdrawal_factor(animal, 40), y35)

    # Grid-cell shape check
    t = xr.DataArray([15, 25, 35], dims="time")
    d = xr.DataArray([2, 2, 2], dims="time")
    out = withdrawal_by_gridcell("cattle", t, d)
    assert out.shape == (3,)

    print("✅ self-tests passed.")


if __name__ == "__main__":  # pragma: no cover
    _self_tests()
    plot_withdrawal_curves()

__all__ = [
    "withdrawal_factor",
    "withdrawal_by_gridcell",
    "plot_withdrawal_curves",
    "FACTOR_FNS",
]

