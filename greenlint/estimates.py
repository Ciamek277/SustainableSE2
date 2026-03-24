"""Load benchmark-derived Joules / CO2e / weights per rule from summary.json."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from greenlint.diagnostics import Diagnostic

_DEFAULT_SUMMARY = Path(__file__).resolve().parent.parent / "experiments" / "results" / "summary.json"


def load_summary(path: Path | None = None) -> dict[str, Any]:
    """Load experiments/results/summary.json (or empty defaults if missing)."""
    p = path or _DEFAULT_SUMMARY
    if not p.is_file():
        return {"rules": {}, "note": "No summary.json; run experiments/run_benchmark.py"}
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def estimate_for_code(code: str, summary: dict[str, Any] | None = None) -> tuple[float, float, float]:
    """Return (delta_joules_median, delta_co2_grams_median, weight) for a rule code."""
    data = summary if summary is not None else load_summary()
    rules = data.get("rules") or {}
    entry = rules.get(code) or {}
    j = float(entry.get("delta_joules_median", 0.0) or 0.0)
    co2 = float(entry.get("delta_co2_grams_median", 0.0) or 0.0)
    w = float(entry.get("weight", 1.0) or 1.0)
    return j, co2, w


def attach_estimates(diagnostics: list[Diagnostic], summary: dict[str, Any] | None = None) -> list[Diagnostic]:
    if summary is None:
        summary = load_summary()
    out: list[Diagnostic] = []
    for d in diagnostics:
        j, co2, _ = estimate_for_code(d.code, summary)
        out.append(replace(d, joules_saved=j, co2_grams_saved=co2))
    return out
