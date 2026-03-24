"""ECO5 — unused heavy top-level import (prefer lazy/local import)."""

from __future__ import annotations

import ast

from greenlint.diagnostics import Diagnostic
from greenlint.rules.base import BaseRule

# Modules considered "heavy" for this MVP (stdlib + common scientific stack).
_HEAVY_ROOT = frozenset(
    {
        "multiprocessing",
        "subprocess",
        "threading",
        "concurrent",
        "socket",
        "ssl",
        "ctypes",
        "urllib",
        "http",
        "numpy",
        "pandas",
        "torch",
        "tensorflow",
        "sklearn",
        "matplotlib",
        "requests",
        "PIL",
        "cv2",
        "scipy",
        "skimage",
        "transformers",
    }
)


def _root_module(name: str) -> str:
    return name.split(".", 1)[0]


def _stmt_import_bindings(stmt: ast.stmt) -> list[tuple[str, int]]:
    """(local_name, lineno) for each bound name."""
    out: list[tuple[str, int]] = []
    if isinstance(stmt, ast.Import):
        for alias in stmt.names:
            local = alias.asname or _root_module(alias.name)
            out.append((local, stmt.lineno))
    elif isinstance(stmt, ast.ImportFrom):
        if stmt.module is None:
            return out
        root = _root_module(stmt.module)
        if root not in _HEAVY_ROOT:
            return out
        for alias in stmt.names:
            if alias.name == "*":
                continue
            local = alias.asname or alias.name
            out.append((local, stmt.lineno))
    return out


def _import_heavy_root(stmt: ast.stmt) -> str | None:
    if isinstance(stmt, ast.Import):
        for alias in stmt.names:
            root = _root_module(alias.name)
            if root in _HEAVY_ROOT:
                return root
    elif isinstance(stmt, ast.ImportFrom) and stmt.module:
        root = _root_module(stmt.module)
        if root in _HEAVY_ROOT:
            return root
    return None


def _name_used(name: str, tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == name:
            return True
        if isinstance(node, ast.Attribute):
            cur: ast.AST = node
            while isinstance(cur, ast.Attribute):
                cur = cur.value
            if isinstance(cur, ast.Name) and cur.id == name:
                return True
    return False


class ECO5Rule(BaseRule):
    code = "ECO5"

    def check(self, tree: ast.AST) -> list[Diagnostic]:
        if not isinstance(tree, ast.Module):
            return []
        out: list[Diagnostic] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.Import):
                continue
            if _import_heavy_root(stmt) is None:
                continue
            for alias in stmt.names:
                local = alias.asname or _root_module(alias.name)
                if not _name_used(local, tree):
                    out.append(
                        Diagnostic(
                            line=stmt.lineno,
                            code=self.code,
                            message="Unused heavy top-level import.",
                            suggestion="import locally inside the function or block that needs it.",
                        )
                    )
        for stmt in tree.body:
            if not isinstance(stmt, ast.ImportFrom):
                continue
            if _import_heavy_root(stmt) is None:
                continue
            for alias in stmt.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                if not _name_used(local, tree):
                    out.append(
                        Diagnostic(
                            line=stmt.lineno,
                            code=self.code,
                            message="Unused heavy top-level import.",
                            suggestion="import locally inside the function or block that needs it.",
                        )
                    )
        return out
