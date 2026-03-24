"""Shared helpers for GreenLint tests."""

from __future__ import annotations

from pathlib import Path

from greenlint.analyzer import analyze_source


def codes_from_source(source: str) -> set[str]:
    return {d.code for d in analyze_source(source, "<test>")}


def codes_from_file(path: Path) -> set[str]:
    return {d.code for d in analyze_source(path.read_text(encoding="utf-8"), path)}
