from __future__ import annotations

import ast

from greenlint.diagnostics import Diagnostic
from greenlint.rules.base import BaseRule


def _range_len_seq(iter_node: ast.AST) -> ast.AST | None:
    if not isinstance(iter_node, ast.Call):
        return None
    if not isinstance(iter_node.func, ast.Name) or iter_node.func.id != "range":
        return None
    if len(iter_node.args) != 1:
        return None
    inner = iter_node.args[0]
    if not isinstance(inner, ast.Call):
        return None
    if not isinstance(inner.func, ast.Name) or inner.func.id != "len":
        return None
    if len(inner.args) != 1:
        return None
    return inner.args[0]


def _seq_name_id(seq_node: ast.AST) -> str | None:
    if isinstance(seq_node, ast.Name):
        return seq_node.id
    return None


def _body_indexes_seq_with_var(body: list[ast.stmt], seq_id: str, loop_var: str) -> bool:
    for stmt in body:
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Subscript):
                continue
            if not isinstance(node.value, ast.Name) or node.value.id != seq_id:
                continue
            sl = node.slice
            if isinstance(sl, ast.Name) and sl.id == loop_var:
                return True
    return False


class ECO1Rule(BaseRule):
    code = "ECO1"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.For):
                continue
            seq_expr = _range_len_seq(node.iter)
            if seq_expr is None:
                continue
            if not isinstance(node.target, ast.Name):
                continue
            seq_id = _seq_name_id(seq_expr)
            if seq_id is None:
                continue
            if not _body_indexes_seq_with_var(node.body, seq_id, node.target.id):
                continue
            out.append(
                Diagnostic(
                    line=node.lineno,
                    code=self.code,
                    message="range(len(...)) loop with indexing.",
                    suggestion="use `for item in lst` or `enumerate()`.",
                )
            )
        return out
