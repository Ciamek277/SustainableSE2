"""Run a benchmark script once and return duration + proxy energy/CO2.

``codecarbon.EmissionsTracker`` (hardware / ``powermetrics`` / ``sudo``) is **not**
used: it often breaks in IDE terminals (``BlockingIOError: 35``, ``sudo: unable to
allocate pty``).

**Default:** one ``runpy.run_path``, then duration → rough ``energy_j`` / ``co2_kg``
so bad vs good stay comparable in ``summary.json``.

**Optional:** ``GREENLINT_CODECARBON=1`` tries ``OfflineEmissionsTracker`` around a
**single** run; on any error, falls back to the same duration proxy.
"""

from __future__ import annotations

import os
import runpy
import time
from pathlib import Path
from typing import Any


def proxy_scale_factors() -> tuple[float, float]:
    """(joules per second, kg CO2 per second) for the duration proxy.

    Override with ``GREENLINT_PROXY_J_PER_S`` and ``GREENLINT_PROXY_CO2_KG_PER_S``.
    Defaults are higher than bare CPU numbers so coursework summaries read in clearer
    units while **bad vs good ratios** stay the same for a fixed machine.
    """
    j = float(os.environ.get("GREENLINT_PROXY_J_PER_S", "25"))
    c = float(os.environ.get("GREENLINT_PROXY_CO2_KG_PER_S", "5e-7"))
    return j, c


def _proxy_from_duration(dt: float) -> tuple[float, float]:
    jps, cps = proxy_scale_factors()
    energy_j = max(dt * jps, 1e-12)
    co2_kg = max(dt * cps, 1e-18)
    return energy_j, co2_kg


def run_script_measured(path: Path) -> dict[str, Any]:
    """Execute ``path`` as ``__main__``; return duration and monotonic proxy metrics."""
    path = path.resolve()
    use_cc = os.environ.get("GREENLINT_CODECARBON", "").lower() in ("1", "true", "yes")

    if use_cc:
        try:
            from codecarbon import OfflineEmissionsTracker  # type: ignore[import-untyped]

            tracker = OfflineEmissionsTracker(
                country_iso_code=os.environ.get("GREENLINT_COUNTRY", "USA"),
                measure_power_secs=0,
                save_to_file=False,
                save_to_api=False,
                log_level="critical",
            )
            t0 = time.perf_counter()
            tracker.start()
            runpy.run_path(str(path), run_name="__main__")
            tracker.stop()
            dt = time.perf_counter() - t0
            co2_kg = float(getattr(tracker, "final_emissions", 0.0) or 0.0)
            energy_j = 0.0
            kwh = getattr(tracker, "_total_energy", None)
            if kwh is None and hasattr(tracker, "final_emissions_data"):
                fed = getattr(tracker, "final_emissions_data")
                if isinstance(fed, dict):
                    kwh = fed.get("energy_consumed")
            if kwh is not None:
                energy_j = float(kwh) * 3.6e6
            if energy_j <= 0.0 or co2_kg <= 0.0:
                ej, ck = _proxy_from_duration(dt)
                if energy_j <= 0.0:
                    energy_j = ej
                if co2_kg <= 0.0:
                    co2_kg = ck
            return {"duration_s": dt, "energy_j": energy_j, "co2_kg": co2_kg}
        except Exception:
            pass

    t0 = time.perf_counter()
    runpy.run_path(str(path), run_name="__main__")
    dt = time.perf_counter() - t0
    energy_j, co2_kg = _proxy_from_duration(dt)
    return {"duration_s": dt, "energy_j": energy_j, "co2_kg": co2_kg}
