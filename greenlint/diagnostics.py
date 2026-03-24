from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    line: int
    code: str
    message: str
    suggestion: str
    # Benchmark-backed category estimates (filled by analyzer from summary.json).
    joules_saved: float = 0.0
    co2_grams_saved: float = 0.0

    def format_line(self, filepath: str) -> str:
        head = f"{filepath}:{self.line} {self.code} {self.message} Suggestion: {self.suggestion}"
        return (
            f"{head} Estimated saving: {self.joules_saved:.2f} J, "
            f"{self.co2_grams_saved:.3f} g CO2e"
        )
