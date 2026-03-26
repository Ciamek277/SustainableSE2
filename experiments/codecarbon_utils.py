"""Run a benchmark script once: wall-clock time -> proxy energy (no powermetrics/sudo by default)."""

from __future__ import annotations

import os
import runpy
import time
from pathlib import Path
from typing import Any


def proxy_scale_factors() -> tuple[float, float]:
    j = float(os.environ.get("GREENLINT_PROXY_J_PER_S", "25"))
    c = float(os.environ.get("GREENLINT_PROXY_CO2_KG_PER_S", "5e-7"))
    return j, c


def _proxy_from_duration(dt: float) -> tuple[float, float]:
    jps, cps = proxy_scale_factors()
    return max(dt * jps, 1e-12), max(dt * cps, 1e-18)


def run_script_measured(path: Path) -> dict[str, Any]:
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
