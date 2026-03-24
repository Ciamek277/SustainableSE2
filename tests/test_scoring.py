from __future__ import annotations

from greenlint.diagnostics import Diagnostic
from greenlint.scoring import green_score


def test_green_score_bounds() -> None:
    assert green_score([], {}) == 10


def test_green_score_weighted() -> None:
    summary = {"rules": {"ECO1": {"weight": 2.0}}}
    d = [Diagnostic(1, "ECO1", "m", "s")]
    assert green_score(d, summary) == 8
