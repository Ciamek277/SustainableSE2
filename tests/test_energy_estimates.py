"""Tests for estimate attachment and scoring integration with summary.json."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from greenlint.estimates import attach_estimates, load_summary
from greenlint.rules import ALL_RULES
from greenlint.scoring import green_score


def test_attach_estimates_fills_joules_from_summary(tmp_path: Path) -> None:
    summary = {
        "rules": {
            "ECO1": {
                "delta_joules_median": 1.25,
                "delta_co2_grams_median": 0.05,
                "weight": 0.5,
            }
        }
    }
    p = tmp_path / "s.json"
    p.write_text(json.dumps(summary), encoding="utf-8")
    loaded = load_summary(p)

    src = """
lst = [1]
for i in range(len(lst)):
    _ = lst[i]
"""
    tree = ast.parse(src)
    diags = []
    for rule in ALL_RULES:
        diags.extend(rule.check(tree))
    out = attach_estimates(diags, loaded)
    assert len(out) == 1
    assert out[0].joules_saved == 1.25
    assert out[0].co2_grams_saved == 0.05


def test_green_score_uses_weights_from_summary() -> None:
    summary = {"rules": {"ECO1": {"weight": 3.0}}}
    from greenlint.diagnostics import Diagnostic

    d = [Diagnostic(1, "ECO1", "m", "s")]
    assert green_score(d, summary) == 7  # 10 - 3
