from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from greenlint.diagnostics import Diagnostic


def green_score(
    diagnostics: list[Diagnostic],
    summary: dict | None = None,
) -> int:
    """
    Score starts at 10. Subtract each warning's benchmark weight from summary.json.
    Default weight is 1.0 if missing. Result clamped to [0, 10].
    """
    if summary is None:
        from greenlint.estimates import load_summary

        summary = load_summary()

    rules = summary.get("rules") or {}
    penalty = 0.0
    for d in diagnostics:
        entry = rules.get(d.code) or {}
        w = float(entry.get("weight", 1.0) or 1.0)
        penalty += w

    # Truncate toward zero so fractional weights (e.g. 0.5) reduce score predictably.
    score = int(10.0 - penalty)
    return max(0, min(10, score))
