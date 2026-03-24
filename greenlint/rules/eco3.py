from __future__ import annotations

import ast

from greenlint.diagnostics import Diagnostic
from greenlint.rules.base import BaseRule


def _empty_str_assign_name(stmt: ast.stmt) -> str | None:
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return None
    t = stmt.targets[0]
    if not isinstance(t, ast.Name):
        return None
    v = stmt.value
    if isinstance(v, ast.Constant) and v.value == "":
        return t.id
    return None


def _for_augment_adds_to(for_node: ast.For, name: str) -> bool:
    for stmt in for_node.body:
        if isinstance(stmt, ast.AugAssign):
            if isinstance(stmt.target, ast.Name) and stmt.target.id == name:
                if isinstance(stmt.op, ast.Add):
                    return True
    return False


def _iter_statement_lists(tree: ast.AST):
    if isinstance(tree, ast.Module):
        yield tree.body
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.body


class ECO3Rule(BaseRule):
    code = "ECO3"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for stmts in _iter_statement_lists(tree):
            for i, stmt in enumerate(stmts):
                if i == 0 or not isinstance(stmt, ast.For):
                    continue
                var = _empty_str_assign_name(stmts[i - 1])
                if var is None:
                    continue
                if not _for_augment_adds_to(stmt, var):
                    continue
                out.append(
                    Diagnostic(
                        line=stmt.lineno,
                        code=self.code,
                        message="String concatenation in loop.",
                        suggestion="use ''.join(...).",
                    )
                )
        return out
