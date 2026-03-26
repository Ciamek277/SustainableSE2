from __future__ import annotations

from pathlib import Path

from greenlint.cli import main

ROOT = Path(__file__).resolve().parent.parent


def test_cli_clean() -> None:
    assert main([str(ROOT / "benchmarks" / "eco1" / "good.py")]) == 0


def test_cli_warns() -> None:
    assert main([str(ROOT / "benchmarks" / "eco1" / "bad.py")]) == 1
