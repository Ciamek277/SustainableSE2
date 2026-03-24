from __future__ import annotations

import ast

from greenlint.diagnostics import Diagnostic
from greenlint.rules.base import BaseRule


def _in_is_slow_container(comp: ast.AST) -> bool:
    """Membership on set() or {...} is fine; list/tuple/name/... we treat as potentially O(n)."""
    if isinstance(comp, ast.Set):
        return False
    if isinstance(comp, ast.Call) and isinstance(comp.func, ast.Name) and comp.func.id == "set":
        return False
    return True


def _value_is_set_like(value: ast.AST) -> bool:
    if isinstance(value, ast.Set):
        return True
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "set":
        return True
    return False


def _module_level_name_is_set(tree: ast.AST, name: str) -> bool:
    """``x in name`` is O(1) if ``name`` was bound to a set at module scope."""
    if not isinstance(tree, ast.Module):
        return False
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        t = stmt.targets[0]
        if isinstance(t, ast.Name) and t.id == name and _value_is_set_like(stmt.value):
            return True
    return False


def _compare_with_in_on_var(test: ast.AST, loop_var: str, tree: ast.AST) -> bool:
    if not isinstance(test, ast.Compare):
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != loop_var:
        return False
    for op, comp in zip(test.ops, test.comparators):
        if not isinstance(op, ast.In):
            continue
        if isinstance(comp, ast.Name) and _module_level_name_is_set(tree, comp.id):
            continue
        if _in_is_slow_container(comp):
            return True
    return False


def _for_body_has_in_test_on_var(for_node: ast.For, loop_var: str, tree: ast.AST) -> bool:
    for stmt in for_node.body:
        if isinstance(stmt, ast.If) and _compare_with_in_on_var(stmt.test, loop_var, tree):
            return True
    return False


class ECO4Rule(BaseRule):
    code = "ECO4"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.For):
                continue
            if not isinstance(node.target, ast.Name):
                continue
            if not _for_body_has_in_test_on_var(node, node.target.id, tree):
                continue
            out.append(
                Diagnostic(
                    line=node.lineno,
                    code=self.code,
                    message="Membership check against a sequence inside a loop.",
                    suggestion="use a set for membership tests.",
                )
            )
        return out
