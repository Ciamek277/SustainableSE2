"""ECO1–ECO7 checks (AST). One module to keep the student project small."""

from __future__ import annotations

import ast

from greenlint.diagnostics import Diagnostic


def _stmt_bodies(tree: ast.AST):
    if isinstance(tree, ast.Module):
        yield tree.body
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.body


def run_rules(tree: ast.AST) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    out.extend(_eco1_range_len(tree))
    out.extend(_eco2_append_loop(tree))
    out.extend(_eco3_string_concat(tree))
    out.extend(_eco4_membership(tree))
    out.extend(_eco5_unused_import(tree))
    out.extend(_eco6_iterrows(tree))
    out.extend(_eco7_apply(tree))
    return out


# --- ECO1 ---


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


def _body_indexes_seq(body: list[ast.stmt], seq_id: str, loop_var: str) -> bool:
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


def _eco1_range_len(tree: ast.AST) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        seq_expr = _range_len_seq(node.iter)
        if seq_expr is None or not isinstance(node.target, ast.Name):
            continue
        if not isinstance(seq_expr, ast.Name):
            continue
        seq_id = seq_expr.id
        if not _body_indexes_seq(node.body, seq_id, node.target.id):
            continue
        out.append(
            Diagnostic(
                line=node.lineno,
                code="ECO1",
                message="range(len(...)) loop with indexing.",
                suggestion="use `for item in lst` or `enumerate()`.",
            )
        )
    return out


# --- ECO2 ---


def _empty_list_name(stmt: ast.stmt) -> str | None:
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return None
    t = stmt.targets[0]
    if not isinstance(t, ast.Name):
        return None
    if isinstance(stmt.value, ast.List) and len(stmt.value.elts) == 0:
        return t.id
    return None


def _for_only_appends(for_node: ast.For, name: str) -> bool:
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


def _eco2_append_loop(tree: ast.AST) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for stmts in _stmt_bodies(tree):
        for i, stmt in enumerate(stmts):
            if i == 0 or not isinstance(stmt, ast.For):
                continue
            list_name = _empty_list_name(stmts[i - 1])
            if list_name is None or not _for_only_appends(stmt, list_name):
                continue
            out.append(
                Diagnostic(
                    line=stmt.lineno,
                    code="ECO2",
                    message="Building a list with .append() in a loop.",
                    suggestion="use a list comprehension.",
                )
            )
    return out


# --- ECO3 ---


def _empty_str_name(stmt: ast.stmt) -> str | None:
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return None
    t = stmt.targets[0]
    if not isinstance(t, ast.Name):
        return None
    v = stmt.value
    if isinstance(v, ast.Constant) and v.value == "":
        return t.id
    return None


def _for_augments_str(for_node: ast.For, name: str) -> bool:
    for stmt in for_node.body:
        if isinstance(stmt, ast.AugAssign):
            if isinstance(stmt.target, ast.Name) and stmt.target.id == name:
                if isinstance(stmt.op, ast.Add):
                    return True
    return False


def _eco3_string_concat(tree: ast.AST) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for stmts in _stmt_bodies(tree):
        for i, stmt in enumerate(stmts):
            if i == 0 or not isinstance(stmt, ast.For):
                continue
            var = _empty_str_name(stmts[i - 1])
            if var is None or not _for_augments_str(stmt, var):
                continue
            out.append(
                Diagnostic(
                    line=stmt.lineno,
                    code="ECO3",
                    message="String concatenation in loop.",
                    suggestion="collect strings in a list and use ''.join(...).",
                )
            )
    return out


# --- ECO4 ---


def _in_is_slow(comp: ast.AST) -> bool:
    if isinstance(comp, ast.Set):
        return False
    if isinstance(comp, ast.Call) and isinstance(comp.func, ast.Name) and comp.func.id == "set":
        return False
    return True


def _assigns_set_at_module(mod: ast.Module, name: str) -> bool:
    for stmt in mod.body:
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        t = stmt.targets[0]
        if not isinstance(t, ast.Name) or t.id != name:
            continue
        v = stmt.value
        if isinstance(v, ast.Set):
            return True
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "set":
            return True
    return False


def _slow_in_compare(test: ast.AST, loop_var: str, tree: ast.AST) -> bool:
    if not isinstance(test, ast.Compare):
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != loop_var:
        return False
    mod = tree if isinstance(tree, ast.Module) else None
    for op, comp in zip(test.ops, test.comparators):
        if not isinstance(op, ast.In):
            continue
        if isinstance(comp, ast.Name) and mod is not None and _assigns_set_at_module(mod, comp.id):
            continue
        if _in_is_slow(comp):
            return True
    return False


def _eco4_membership(tree: ast.AST) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.target, ast.Name):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.If) and _slow_in_compare(stmt.test, node.target.id, tree):
                out.append(
                    Diagnostic(
                        line=node.lineno,
                        code="ECO4",
                        message="Membership check against a sequence inside a loop.",
                        suggestion="use a set for membership tests.",
                    )
                )
                break
    return out


# --- ECO5 ---

_HEAVY = frozenset(
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


def _root(name: str) -> str:
    return name.split(".", 1)[0]


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


def _eco5_unused_import(tree: ast.AST) -> list[Diagnostic]:
    if not isinstance(tree, ast.Module):
        return []
    out: list[Diagnostic] = []
    for stmt in tree.body:
        if not isinstance(stmt, ast.Import):
            continue
        for alias in stmt.names:
            if _root(alias.name) not in _HEAVY:
                continue
            local = alias.asname or _root(alias.name)
            if not _name_used(local, tree):
                out.append(
                    Diagnostic(
                        line=stmt.lineno,
                        code="ECO5",
                        message="Unused heavy top-level import.",
                        suggestion="import locally inside the function or block that needs it.",
                    )
                )
    for stmt in tree.body:
        if not isinstance(stmt, ast.ImportFrom) or not stmt.module:
            continue
        if _root(stmt.module) not in _HEAVY:
            continue
        for alias in stmt.names:
            if alias.name == "*":
                continue
            local = alias.asname or alias.name
            if not _name_used(local, tree):
                out.append(
                    Diagnostic(
                        line=stmt.lineno,
                        code="ECO5",
                        message="Unused heavy top-level import.",
                        suggestion="import locally inside the function or block that needs it.",
                    )
                )
    return out


# --- ECO6 / ECO7 ---


def _eco6_iterrows(tree: ast.AST) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "iterrows"
        ):
            out.append(
                Diagnostic(
                    line=node.lineno,
                    code="ECO6",
                    message="Using pandas iterrows() for iteration.",
                    suggestion="use vectorized column operations or .to_numpy() / .values instead.",
                )
            )
    return out


def _eco7_apply(tree: ast.AST) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "apply"
        ):
            out.append(
                Diagnostic(
                    line=node.lineno,
                    code="ECO7",
                    message="pandas apply() on a simple expression.",
                    suggestion="use vectorized arithmetic or .str / numpy ufuncs instead of apply().",
                )
            )
    return out
