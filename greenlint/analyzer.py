from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from greenlint.diagnostics import Diagnostic
from greenlint.rules import run_rules

_DEFAULT_SUMMARY = Path(__file__).resolve().parent.parent / "experiments" / "results" / "summary.json"


def load_summary(path: Path | None = None) -> dict[str, Any]:
    p = path or _DEFAULT_SUMMARY
    if not p.is_file():
        return {"rules": {}, "note": "No summary.json; run experiments/run_benchmark.py"}
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def attach_estimates(diagnostics: list[Diagnostic], summary: dict[str, Any] | None = None) -> list[Diagnostic]:
    if summary is None:
        summary = load_summary()
    rules = summary.get("rules") or {}
    out: list[Diagnostic] = []
    for d in diagnostics:
        entry = rules.get(d.code) or {}
        j = float(entry.get("delta_joules_median", 0.0) or 0.0)
        co2 = float(entry.get("delta_co2_grams_median", 0.0) or 0.0)
        out.append(replace(d, joules_saved=j, co2_grams_saved=co2))
    return out


def green_score(diagnostics: list[Diagnostic], summary: dict[str, Any] | None = None) -> int:
    if summary is None:
        summary = load_summary()
    rules = summary.get("rules") or {}
    penalty = 0.0
    for d in diagnostics:
        entry = rules.get(d.code) or {}
        penalty += float(entry.get("weight", 1.0) or 1.0)
    return max(0, min(10, int(10.0 - penalty)))


def analyze_source(
    source: str,
    path: str | Path = "<string>",
    *,
    summary_path: Path | None = None,
) -> list[Diagnostic]:
    tree = ast.parse(source, filename=str(path))
    diagnostics = run_rules(tree)
    diagnostics.sort(key=lambda d: (d.line, d.code))
    summary = load_summary(summary_path) if summary_path else None
    return attach_estimates(diagnostics, summary)


def analyze_file(path: Path, *, summary_path: Path | None = None) -> list[Diagnostic]:
    text = path.read_text(encoding="utf-8")
    return analyze_source(text, path, summary_path=summary_path)
