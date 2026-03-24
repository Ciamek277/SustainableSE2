"""ECO7 — simple pandas Series/DataFrame.apply() where vectorized ops suffice."""

from __future__ import annotations

import ast

from greenlint.diagnostics import Diagnostic
from greenlint.rules.base import BaseRule


def _is_apply_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "apply"
    )


class ECO7Rule(BaseRule):
    code = "ECO7"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for node in ast.walk(tree):
            if not _is_apply_call(node):
                continue
            out.append(
                Diagnostic(
                    line=node.lineno,
                    code=self.code,
                    message="pandas apply() on a simple expression.",
                    suggestion="use vectorized arithmetic or .str / numpy ufuncs instead of apply().",
                )
            )
        return out
