"""Rules + benchmark files."""

from __future__ import annotations

from pathlib import Path

import pytest

from greenlint.analyzer import analyze_file
from conftest import codes_from_source

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks"


@pytest.mark.parametrize(
    "eco",
    ["eco1", "eco2", "eco3", "eco4", "eco5", "eco6", "eco7"],
)
def test_bad_fires(eco: str) -> None:
    diags = analyze_file(BENCH / eco / "bad.py")
    code = f"ECO{eco[3:]}"
    assert any(d.code == code for d in diags)


@pytest.mark.parametrize(
    "eco",
    ["eco1", "eco2", "eco3", "eco4", "eco5", "eco6", "eco7"],
)
def test_good_clean(eco: str) -> None:
    assert not analyze_file(BENCH / eco / "good.py")


def test_eco1_snippets() -> None:
    assert "ECO1" in codes_from_source(
        """
lst = [1, 2, 3]
for i in range(len(lst)):
    _ = lst[i]
"""
    )
    assert "ECO1" not in codes_from_source("for x in seq:\n    _ = x\n")


def test_eco2_snippets() -> None:
    src = """
items = range(10)
out = []
for x in items:
    out.append(x * 2)
"""
    assert "ECO2" in codes_from_source(src)
    assert "ECO2" not in codes_from_source(
        """
items = range(10)
out = []
x = 1
for x in items:
    out.append(x)
"""
    )


def test_eco3_snippets() -> None:
    assert "ECO3" in codes_from_source(
        """
items = ["a", "b"]
s = ""
for x in items:
    s += str(x)
"""
    )


def test_eco4_snippets() -> None:
    assert "ECO4" in codes_from_source(
        """
for x in range(3):
    if x in [1, 2]:
        pass
"""
    )
    assert "ECO4" not in codes_from_source(
        """
for x in range(3):
    if x in {1, 2}:
        pass
"""
    )


def test_eco5_snippets() -> None:
    assert "ECO5" in codes_from_source(
        """
import multiprocessing
x = 1
"""
    )
    assert "ECO5" not in codes_from_source(
        """
import os
x = 1
"""
    )


def test_eco6_snippets() -> None:
    assert "ECO6" in codes_from_source(
        """
import pandas as pd
df = pd.DataFrame({"a": [1]})
for _, row in df.iterrows():
    _ = row["a"]
"""
    )


def test_eco7_snippets() -> None:
    assert "ECO7" in codes_from_source(
        """
import pandas as pd
df = pd.DataFrame({"x": [1, 2]})
df["y"] = df["x"].apply(lambda v: v + 1)
"""
    )


def test_two_rules_one_file() -> None:
    src = """
lst = [1, 2, 3]
for i in range(len(lst)):
    _ = lst[i]
values = [1, 2, 3]
for x in values:
    if x in [2]:
        pass
"""
    codes = codes_from_source(src)
    assert "ECO1" in codes and "ECO4" in codes
