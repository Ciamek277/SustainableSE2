from __future__ import annotations

import ast
from pathlib import Path

from greenlint.diagnostics import Diagnostic
from greenlint.rules import ALL_RULES


def analyze_source(source: str, path: str | Path = "<string>") -> list[Diagnostic]:
    tree = ast.parse(source, filename=str(path))
    diagnostics: list[Diagnostic] = []
    for rule in ALL_RULES:
        diagnostics.extend(rule.check(tree))
    diagnostics.sort(key=lambda d: (d.line, d.code))
    return diagnostics


def analyze_file(path: Path) -> list[Diagnostic]:
    text = path.read_text(encoding="utf-8")
    return analyze_source(text, path)
