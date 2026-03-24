"""ECO6 — pandas DataFrame.iterrows() (prefer vectorized ops)."""

from __future__ import annotations

import ast

from greenlint.diagnostics import Diagnostic
from greenlint.rules.base import BaseRule


def _is_iterrows_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "iterrows"
    )


class ECO6Rule(BaseRule):
    code = "ECO6"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for node in ast.walk(tree):
            if _is_iterrows_call(node):
                out.append(
                    Diagnostic(
                        line=node.lineno,
                        code=self.code,
                        message="Using pandas iterrows() for iteration.",
                        suggestion="use vectorized column operations or .to_numpy() / .values instead.",
                    )
                )
        return out
