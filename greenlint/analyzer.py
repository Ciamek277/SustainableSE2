from __future__ import annotations

import ast
from pathlib import Path

from greenlint.diagnostics import Diagnostic
from greenlint.estimates import attach_estimates, load_summary
from greenlint.rules import ALL_RULES


def analyze_source(
    source: str,
    path: str | Path = "<string>",
    *,
    summary_path: Path | None = None,
) -> list[Diagnostic]:
    tree = ast.parse(source, filename=str(path))
    diagnostics: list[Diagnostic] = []
    for rule in ALL_RULES:
        diagnostics.extend(rule.check(tree))
    diagnostics.sort(key=lambda d: (d.line, d.code))
    summary = load_summary(summary_path) if summary_path else None
    return attach_estimates(diagnostics, summary)


def analyze_file(path: Path, *, summary_path: Path | None = None) -> list[Diagnostic]:
    text = path.read_text(encoding="utf-8")
    return analyze_source(text, path, summary_path=summary_path)
