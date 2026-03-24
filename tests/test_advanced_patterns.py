"""Advanced parametrized tests: clearer bad vs good separation per rule."""

from __future__ import annotations

import pytest

from tests.conftest import codes_from_source


class TestECO1RangeLen:
    @pytest.mark.parametrize(
        "src,expected",
        [
            (
                """
lst = [1, 2, 3]
for i in range(len(lst)):
    _ = lst[i]
""",
                True,
            ),
            (
                """
items = [1, 2, 3]
for i in range(len(items)):
    x = items[i]
""",
                True,
            ),
        ],
    )
    def test_should_flag(self, src: str, expected: bool) -> None:
        codes = codes_from_source(src)
        assert ("ECO1" in codes) is expected

    @pytest.mark.parametrize(
        "src",
        [
            "for x in seq:\n    _ = x\n",
            "for i, v in enumerate(lst):\n    _ = lst[i]\n",
            "for i in range(3):\n    pass\n",
        ],
    )
    def test_should_not_flag(self, src: str) -> None:
        assert "ECO1" not in codes_from_source(src)


class TestECO2AppendLoop:
    def test_flags_only_append_body(self) -> None:
        src = """
items = range(10)
out = []
for x in items:
    out.append(x * 2)
"""
        assert "ECO2" in codes_from_source(src)

    def test_no_flag_if_not_immediately_after_empty_list(self) -> None:
        src = """
items = range(10)
out = []
x = 1
for x in items:
    out.append(x)
"""
        assert "ECO2" not in codes_from_source(src)

    def test_no_flag_if_not_only_append(self) -> None:
        src = """
items = range(10)
out = []
for x in items:
    out.append(x)
    print(x)
"""
        assert "ECO2" not in codes_from_source(src)


class TestECO3StringConcat:
    def test_flags_augment_add(self) -> None:
        src = """
items = ["a", "b"]
s = ""
for x in items:
    s += str(x)
"""
        assert "ECO3" in codes_from_source(src)

    def test_no_flag_without_prior_empty_str(self) -> None:
        src = """
s = "x"
for x in items:
    s += str(x)
"""
        assert "ECO3" not in codes_from_source(src)


class TestECO4Membership:
    def test_flags_list_literal_in_loop(self) -> None:
        src = """
for x in range(3):
    if x in [1, 2]:
        pass
"""
        assert "ECO4" in codes_from_source(src)

    def test_no_flag_set_literal(self) -> None:
        src = """
for x in range(3):
    if x in {1, 2}:
        pass
"""
        assert "ECO4" not in codes_from_source(src)


class TestECO5HeavyImport:
    def test_unused_multiprocessing(self) -> None:
        src = """
import multiprocessing
x = 1
"""
        assert "ECO5" in codes_from_source(src)

    def test_used_multiprocessing(self) -> None:
        src = """
import multiprocessing
x = multiprocessing.cpu_count()
"""
        assert "ECO5" not in codes_from_source(src)

    def test_unused_os_not_heavy(self) -> None:
        src = """
import os
x = 1
"""
        assert "ECO5" not in codes_from_source(src)


class TestECO6Iterrows:
    def test_detects_iterrows(self) -> None:
        src = """
import pandas as pd
df = pd.DataFrame({"a": [1]})
for _, row in df.iterrows():
    _ = row["a"]
"""
        assert "ECO6" in codes_from_source(src)


class TestECO7Apply:
    def test_detects_apply(self) -> None:
        src = """
import pandas as pd
df = pd.DataFrame({"x": [1, 2]})
df["y"] = df["x"].apply(lambda v: v + 1)
"""
        assert "ECO7" in codes_from_source(src)


class TestCombinedRules:
    """One file can trigger multiple rules."""

    def test_eco1_and_eco4(self) -> None:
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
        assert "ECO1" in codes
        assert "ECO4" in codes
