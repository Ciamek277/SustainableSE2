from __future__ import annotations

from pathlib import Path

from greenlint.analyzer import analyze_file

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks"


def test_eco3_bad_triggers() -> None:
    diags = analyze_file(BENCH / "eco3" / "bad.py")
    assert any(d.code == "ECO3" for d in diags)


def test_eco3_good_clean() -> None:
    diags = analyze_file(BENCH / "eco3" / "good.py")
    assert not diags
