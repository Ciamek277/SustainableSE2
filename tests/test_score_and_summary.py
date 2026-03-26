import ast
import json
from pathlib import Path

from greenlint.analyzer import attach_estimates, green_score, load_summary
from greenlint.rules import run_rules


def test_attach_estimates(tmp_path: Path) -> None:
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

    tree = ast.parse(
        """
lst = [1]
for i in range(len(lst)):
    _ = lst[i]
"""
    )
    diags = run_rules(tree)
    out = attach_estimates(diags, loaded)
    assert len(out) == 1
    assert out[0].joules_saved == 1.25
    assert out[0].co2_grams_saved == 0.05


def test_green_score_weights() -> None:
    from greenlint.diagnostics import Diagnostic

    summary = {"rules": {"ECO1": {"weight": 3.0}}}
    d = [Diagnostic(1, "ECO1", "m", "s")]
    assert green_score(d, summary) == 7


def test_green_score_empty() -> None:
    assert green_score([], {}) == 10
