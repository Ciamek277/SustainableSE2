"""Median / delta helpers for benchmark CSV rows."""

from __future__ import annotations

from statistics import median


def median_float(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(median(values))
