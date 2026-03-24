from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    line: int
    code: str
    message: str
    suggestion: str

    def format_line(self, filepath: str) -> str:
        return f"{filepath}:{self.line} {self.code} {self.message} Suggestion: {self.suggestion}"
