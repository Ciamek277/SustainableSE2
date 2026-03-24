from __future__ import annotations

from pathlib import Path

from greenlint.cli import main

ROOT = Path(__file__).resolve().parent.parent


def test_cli_exits_zero_on_clean_file() -> None:
    p = ROOT / "benchmarks" / "eco1" / "good.py"
    assert main([str(p)]) == 0


def test_cli_exits_nonzero_on_issues() -> None:
    p = ROOT / "benchmarks" / "eco1" / "bad.py"
    assert main([str(p)]) == 1
