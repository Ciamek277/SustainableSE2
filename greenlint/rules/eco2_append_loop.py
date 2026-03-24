from __future__ import annotations

import ast

from greenlint.diagnostics import Diagnostic
from greenlint.rules.base import BaseRule


def _empty_list_assign_name(stmt: ast.stmt) -> str | None:
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return None
    t = stmt.targets[0]
    if not isinstance(t, ast.Name):
        return None
    if isinstance(stmt.value, ast.List) and len(stmt.value.elts) == 0:
        return t.id
    return None


def _for_only_appends_to(for_node: ast.For, name: str) -> bool:
    if not for_node.body:
        return False
    for stmt in for_node.body:
        if not isinstance(stmt, ast.Expr):
            return False
        call = stmt.value
        if not isinstance(call, ast.Call):
            return False
        func = call.func
        if not isinstance(func, ast.Attribute) or func.attr != "append":
            return False
        if not isinstance(func.value, ast.Name) or func.value.id != name:
            return False
    return True


def _iter_statement_lists(tree: ast.AST):
    if isinstance(tree, ast.Module):
        yield tree.body
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.body


class ECO2Rule(BaseRule):
    code = "ECO2"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for stmts in _iter_statement_lists(tree):
            for i, stmt in enumerate(stmts):
                if i == 0 or not isinstance(stmt, ast.For):
                    continue
                list_name = _empty_list_assign_name(stmts[i - 1])
                if list_name is None:
                    continue
                if not _for_only_appends_to(stmt, list_name):
                    continue
                out.append(
                    Diagnostic(
                        line=stmt.lineno,
                        code=self.code,
                        message="Building a list with .append() in a loop.",
                        suggestion="use a list comprehension.",
                    )
                )
        return out
