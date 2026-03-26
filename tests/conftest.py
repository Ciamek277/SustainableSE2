from __future__ import annotations

from greenlint.analyzer import analyze_source


def codes_from_source(source: str) -> set[str]:
    return {d.code for d in analyze_source(source, "<test>")}
