from __future__ import annotations

from pathlib import Path

import pytest

from greenlint.analyzer import analyze_file

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks"


@pytest.mark.parametrize(
    "eco",
    ["eco1", "eco2", "eco3", "eco4"],
)
def test_bad_files_have_warnings(eco: str) -> None:
    path = BENCH / eco / "bad.py"
    diags = analyze_file(path)
    codes = {d.code for d in diags}
    assert eco.upper() in codes


@pytest.mark.parametrize(
    "eco",
    ["eco1", "eco2", "eco3", "eco4"],
)
def test_good_files_clean(eco: str) -> None:
    path = BENCH / eco / "good.py"
    diags = analyze_file(path)
    assert not diags, f"expected no diagnostics, got: {diags!r}"


def test_green_score_helpers() -> None:
    from greenlint.scoring import green_score

    assert green_score(0) == 10
    assert green_score(1) == 9
    assert green_score(15) == 0
