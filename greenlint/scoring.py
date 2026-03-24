from __future__ import annotations


def green_score(warning_count: int) -> int:
    """Score starts at 10; subtract 1 per warning (not below 0)."""
    return max(0, 10 - warning_count)
