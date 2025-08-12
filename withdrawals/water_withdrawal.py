# -*- coding: utf-8 -*-
"""
Created on Sun May 11 14:14:44 2025

@author: Njesh
"""
"""water_withdrawal.py – clean, HPC‑friendly utilities for livestock water demand
--------------------------------------------------------------------------
This module converts **air temperature** to **livestock water‑withdrawal
rates** (litres per head per day) using your **measured values** at
15 °C, 25 °C, 35 °C and a linear relation anchored at 15 °C and 35 °C.
It then multiplies those rates by a spatial density grid so you can
aggregate withdrawals **per grid‑cell** on an HPC cluster.

🔹 *All placeholder curves have been replaced with your real data.*

Key features
============
* **Temperature clipping** – inputs are clipped to 15 ≤ T ≤ 35 °C.
* **Named factor functions** built from your data (exact at 15 °C & 35 °C).
* **Vectorised & Dask‑ready** – drop‑in for xarray / NumPy / Dask.
* **Dotted‑line diagnostic plot** – quick visual sanity check.
* **Stub for ``micropip``** so imports never fail outside Pyodide.

Quick usage
-----------
```python
from water_withdrawal import withdrawal_factor, withdrawal_by_gridcell

print(withdrawal_factor("Cattle", 27.3))  # litres / head / day
```
Replace the density & temperature `xarray` objects with your own and run
`withdrawal_by_gridcell` in parallel on your cluster.
"""

# NOTE: The previous version used ``from __future__ import annotations``.
# That statement must appear at the very top of a file, and some users
# embed this module inside larger scripts where other code precedes it.
# Since Python ≥ 3.11 enables postponed‑evaluation of annotations by
# default—and earlier versions can handle our type hints without the
# future import—we simply removed it to avoid the SyntaxError you saw.

from typing import Callable, Mapping, Union

# ---------------------------------------------------------------------------
# Optional dependency shim – keeps notebooks happy if ``micropip`` is missing
# ---------------------------------------------------------------------------

import sys
import types

if "micropip" not in sys.modules:  # pragma: no cover – executed only if absent
    micropip_stub = types.ModuleType("micropip")

    def _unsupported(*_args, **_kwargs):  # noqa: D401, ANN001 – stub helper
        """Raise helpful error guiding the user to install with pip."""
        raise ModuleNotFoundError(
            "The 'micropip' package is unavailable in this environment. "
            "Install dependencies with pip (CPython) or load 'micropip' in Pyodide."
        )

    micropip_stub.install = _unsupported  # type: ignore[attr-defined]
    sys.modules["micropip"] = micropip_stub

# ---------------------------------------------------------------------------
# Scientific stack
# ---------------------------------------------------------------------------

import numpy as np  # type: ignore
import xarray as xr  # type: ignore
import os
import sys
import types
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb


NumberArray = Union[float, np.ndarray]
#os.makedirs(plots, exist_ok=True)

# ---------------------------------------------------------------------------
# Real withdrawal values provided by the user (litres / head / day)
#   Index 0 → 15 °C, 1 → 25 °C, 2 → 35 °C
# ---------------------------------------------------------------------------

_WITHDRAWAL_DATA = {
    "cattle":  np.array([102.8, 114.8, 126.8]),
    "goats":   np.array([7.6,   9.6,   11.9 ]),
    "sheep":   np.array([8.7,   12.9,  20.1 ]),
    "chicken": np.array([0.177, 0.331, 0.62 ]),
    "pig":     np.array([17.2,  28.3,  46.7 ]),
    "buffalo": np.array([56.2,  71.27, 85.23]),
    "horses":  np.array([31.81, 55.51, 90.84 ]),
    "ducks":   np.array([0.36,  0.7,   1.33 ]),
}

# ---------------------------------------------------------------------------
# Helper to build linear functions anchored at 15 °C and 35 °C
#Builds a straight line between 15 °C and 35 °C so the model can guess the litres/head/day at any temperature in between.
# ---------------------------------------------------------------------------

def _make_factor_fn(y15: float, y35: float) -> Callable[[NumberArray], NumberArray]:
    """Return f(temp) that hits *y15* at 15 °C and *y35* at 35 °C."""
    slope = (y35 - y15) / 20.0  # °C span (35‑15)

    def _fn(temp: NumberArray) -> NumberArray:  # noqa: D401 – internal helper
        return y15 + slope * (np.asarray(temp) - 15.0)

    _fn.__doc__ = f"Linear withdrawal factor anchored at 15 °C ({y15} L) and 35 °C ({y35} L)."
    return _fn

# ---------------------------------------------------------------------------
# Generate factor functions dynamically from the data above
# ---------------------------------------------------------------------------

FACTOR_FNS: Mapping[str, Callable[[NumberArray], NumberArray]] = {
    animal: _make_factor_fn(values[0], values[2])
    for animal, values in _WITHDRAWAL_DATA.items()
}

# ---------------------------------------------------------------------------
# Public API.
#Takes one temperature (or an array) → clips it to 15–35 °C → returns litres per head per day for that animal.
# ---------------------------------------------------------------------------

def withdrawal_factor(animal: str, temperature: NumberArray) -> NumberArray:
    """Litres /head /day for *animal* at *temperature* (°C).

    *temperature* is clipped to 15–35 °C, then passed through the
    species‑specific linear factor function.
    """
    animal=animal.strip().lower()
    if animal not in FACTOR_FNS:
        raise KeyError(f"Unknown animal '{animal}'. Choose from {list(FACTOR_FNS)}.")

    temp_clipped = np.clip(temperature, 15.0, 35.0)
    return FACTOR_FNS[animal](temp_clipped)

# looks up the litres/head/day for every grid cell and day using the line below
# multiplies by the number of animals in that cell → litres/day for the whole cell (still per day).
#The maths runs through xarray, so it can handle big NetCDF files and Dask chunks automatically.

def withdrawal_by_gridcell(
    animal: str,
    temperature: xr.DataArray,
    density: xr.DataArray,
) -> xr.DataArray:
    """Water withdrawals per grid‑cell (litres per **cell** per day).

    Notes
    -----
    *   We wrap :pyfunc:`withdrawal_factor` in a tiny adapter because
        :pyfunc:`xarray.apply_ufunc` passes *data variables* as **positional
        arguments** and anything in *kwargs* as **keyword arguments**. Our
        original function expected the string *animal* as the **first
        positional** argument, which caused *TypeError: multiple values for
        argument 'animal'* when both routes were used.
    *   The adapter takes *temperature* as the first positional argument and
        *animal* only as a keyword, so there’s no clash.
    """
    animal=animal.strip().lower()
    # ---- tiny adapter so apply_ufunc sees the right signature ----
    def _vec(temp: NumberArray, *, animal: str) -> NumberArray:  # noqa: D401
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

# ---------------------------------------------------------------------------
# Diagnostic plot
# ---------------------------------------------------------------------------

def plot_withdrawal_curves(temperature_range: np.ndarray | None = None) -> None:  # noqa: D401
    """Plot dotted lines of withdrawal vs temperature for every animal."""

    import matplotlib.pyplot as plt  # postponed heavy import

    if temperature_range is None:
        temperature_range = np.linspace(15, 35, 400)

    plt.figure(figsize=(7, 4))
    for animal, fn in FACTOR_FNS.items():
        plt.plot(
            temperature_range,
            fn(temperature_range),
            linestyle=":",  # dotted
            label=animal,
        )

    plt.xlabel(" Temperature (°C)")
    plt.ylabel("Water withdrawal (L/head/day)")
    plt.title("Livestock water use intensity vs temperature )")
    plt.legend(ncol=2, fontsize="small")
    plt.tight_layout()

    # ensure ./plots exists
    os.makedirs("plots2", exist_ok=True)
    plt.savefig("plots2/my_result.png", dpi=300, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# Self‑tests – verifies new curves hit the provided data exactly at 15 °C & 35 °C

def _self_tests() -> None:  # pragma: no cover – light runtime checks
    """Sanity checks covering clipping & data anchoring."""

    for animal, values in _WITHDRAWAL_DATA.items():
        y15, _, y35 = values
        assert np.isclose(withdrawal_factor(animal, 15), y15), f"{animal} 15 °C mismatch"
        assert np.isclose(withdrawal_factor(animal, 35), y35), f"{animal} 35 °C mismatch"
        assert np.isclose(withdrawal_factor(animal, 10), y15), f"{animal} clip‑low failed"
        assert np.isclose(withdrawal_factor(animal, 40), y35), f"{animal} clip‑high failed"

    # Quick grid‑cell shape check
    temps = xr.DataArray([15, 25, 35], dims="time")
    dens  = xr.DataArray([2, 2, 2], dims="time")
    res   = withdrawal_by_gridcell("cattle", temps, dens)
    assert res.shape == (3,), "Grid‑cell multiplication failed"

    print("✅ All self‑tests passed.")

if __name__ == "__main__":  # pragma: no cover
    _self_tests()
    # Uncomment to display the dotted‑line plot (requires Matplotlib)
    plot_withdrawal_curves()


__all__ = [
    "withdrawal_factor",
    "withdrawal_by_gridcell",
    "plot_withdrawal_curves",
    "FACTOR_FNS",
]


#plot_withdrawal_curves()


