# GreenLint

GreenLint is a small, **pip-installable** command-line tool for a university course project. It scans Python source files, parses them with Python’s built-in **`ast`** module, and reports a fixed set of **energy-related anti-patterns**. The tool does **not** measure real electrical power or joules; it flags coding patterns that usually imply **extra work on the CPU**, which is used in the course as a **proxy** for “less green” code.

The implementation is intentionally **minimal**: four rules (ECO1–ECO4), a simple per-file score, no database, no configuration file format, and no plugin system.

---

## What GreenLint does

1. Accepts a **path** to a `.py` file or a **directory** (all `*.py` files under it are scanned, sorted by path).
2. Reads each file as **UTF-8** text and parses it with **`ast.parse`**.
3. Runs four static checks implemented as separate rule modules.
4. For each file, prints **one line per warning**, then a **Green Score** for that file.
5. Uses **exit codes**: `0` if every analyzed file had no diagnostics; `1` if any diagnostics or any syntax error in a file; `2` if the given path does not exist.

If a file fails to parse, GreenLint prints a **syntax error** message on **stderr**, sets the exit code to **1**, and **continues** with the remaining files. No Green Score line is printed for a file that was not successfully parsed.

---

## How we implement it

This section is the **implementation story**: what runs in what order, **why** we use the AST, and the **actual project code** (as of this repository) so you can tie the report to the source.

### End-to-end pipeline

1. **`greenlint` console script** — defined in `pyproject.toml` as `greenlint.cli:main`. That function parses CLI arguments, gathers paths, and drives the rest.
2. **Discover files** — `_collect_py_files` returns either a single `.py` file or every `*.py` under a directory (sorted).
3. **Per file:** read text with UTF-8, call **`analyze_file`**, which calls **`ast.parse`** to build a module AST, then runs **every rule** on that same tree.
4. **Each rule** returns a list of **`Diagnostic`** objects (line number, code, message, suggestion). The analyzer **concatenates** those lists and **sorts** by `(line, code)` so output order is stable.
5. **Print** each diagnostic with **`Diagnostic.format_line`**, then compute **`green_score(len(diagnostics))`** and print `Green Score: …`.
6. **Syntax errors** from `ast.parse` are **not** allowed to crash the whole run: the CLI catches **`SyntaxError`**, logs to stderr, sets exit code `1`, and moves to the next file.

We **never execute** user code. Everything is **static analysis** on the AST.

### Why `ast` instead of text search

Rules care about **structure**: e.g. “this `for` loop’s iterator is exactly `range(len(x))`” or “this `if` compares with `in`”. Regexes are brittle; the AST gives typed nodes (`ast.For`, `ast.Call`, `ast.Compare`, …) so the checks are ordinary Python `isinstance` tests and tree walks.

### Packaging: how `greenlint` becomes a command

The wheel/sdist is built with **Hatchling** (see `[build-system]` in `pyproject.toml`). The app registers a console script:

```toml
[project.scripts]
greenlint = "greenlint.cli:main"
```

Installing the package (editable or not) registers that entry point so the shell can run `greenlint`. You can also run **`python -m greenlint`** via `greenlint/__main__.py`.

### The `Diagnostic` type and line format

All rules speak the same output type. From `greenlint/diagnostics.py`:

```python
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
```

### Green Score

From `greenlint/scoring.py`:

```python
from __future__ import annotations


def green_score(warning_count: int) -> int:
    """Score starts at 10; subtract 1 per warning (not below 0)."""
    return max(0, 10 - warning_count)
```

### Analyzer: parse once, run all rules, sort

From `greenlint/analyzer.py`:

```python
from __future__ import annotations

import ast
from pathlib import Path

from greenlint.diagnostics import Diagnostic
from greenlint.rules import ALL_RULES


def analyze_source(source: str, path: str | Path = "<string>") -> list[Diagnostic]:
    tree = ast.parse(source, filename=str(path))
    diagnostics: list[Diagnostic] = []
    for rule in ALL_RULES:
        diagnostics.extend(rule.check(tree))
    diagnostics.sort(key=lambda d: (d.line, d.code))
    return diagnostics


def analyze_file(path: Path) -> list[Diagnostic]:
    text = path.read_text(encoding="utf-8")
    return analyze_source(text, path)
```

### Rule API and registration

Every rule subclasses **`BaseRule`** and implements **`check(self, tree: ast.AST) -> list[Diagnostic]`**.

From `greenlint/rules/base.py`:

```python
from __future__ import annotations

import ast
from abc import ABC, abstractmethod

from greenlint.diagnostics import Diagnostic


class BaseRule(ABC):
    code: str = ""

    @abstractmethod
    def check(self, tree: ast.AST) -> list[Diagnostic]:
        raise NotImplementedError
```

Rules are instantiated in a fixed list in `greenlint/rules/__init__.py`:

```python
from greenlint.rules.eco1 import ECO1Rule
from greenlint.rules.eco2 import ECO2Rule
from greenlint.rules.eco3 import ECO3Rule
from greenlint.rules.eco4 import ECO4Rule

ALL_RULES = [
    ECO1Rule(),
    ECO2Rule(),
    ECO3Rule(),
    ECO4Rule(),
]

__all__ = ["ALL_RULES", "ECO1Rule", "ECO2Rule", "ECO3Rule", "ECO4Rule"]
```

### CLI: file discovery, analysis, printing, exit codes

From `greenlint/cli.py`:

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from greenlint.analyzer import analyze_file
from greenlint.scoring import green_score


def _collect_py_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="greenlint", description="GreenLint — energy-style anti-pattern checker")
    parser.add_argument("path", type=Path, help="File or directory to scan")
    args = parser.parse_args(argv)
    root: Path = args.path
    if not root.exists():
        print(f"greenlint: path not found: {root}", file=sys.stderr)
        return 2

    files = _collect_py_files(root)
    if not files:
        print("greenlint: no Python files found", file=sys.stderr)
        return 1

    exit_code = 0
    for path in files:
        try:
            diagnostics = analyze_file(path)
        except SyntaxError as exc:
            print(f"greenlint: {path}: syntax error: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        if diagnostics:
            exit_code = 1
        display = str(path.resolve())
        for d in diagnostics:
            print(d.format_line(display))
        score = green_score(len(diagnostics))
        print(f"Green Score: {score}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
```

### Example implementation: ECO1 (`ast.walk` over `For` nodes)

ECO1 looks for `for <var> in range(len(<name>)):` and a subscript `<name>[<var>]` somewhere in the loop body. It uses **`ast.walk`** so nested statements inside the `for` body still count.

From `greenlint/rules/eco1.py`:

```python
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
```

### Example implementation: ECO2 (scan consecutive statements in a block)

ECO2 cannot be expressed as “only look at one node”; it needs **`name = []`** immediately before a **`for`** in the **same** block. So it **yields statement lists** (module body, each function body, each class body) and pairs **`stmts[i - 1]`** with **`stmts[i]`**.

From `greenlint/rules/eco2.py`:

```python
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
```

**ECO3** reuses the same `_iter_statement_lists` idea (see `greenlint/rules/eco3.py`): pair **`s = ""`** with a **`for`** whose body does **`s += ...`**.

### Example implementation: ECO4 (`ast.Compare` and `ast.In`)

ECO4 inspects **`if`** tests that are a **`Compare`** with **`in`**, optionally skipping “set-like” right-hand sides (`{...}` or `set(...)`).

From `greenlint/rules/eco4.py`:

```python
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


def _compare_with_in_on_var(test: ast.AST, loop_var: str) -> bool:
    if not isinstance(test, ast.Compare):
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != loop_var:
        return False
    for op, comp in zip(test.ops, test.comparators):
        if isinstance(op, ast.In) and _in_is_slow_container(comp):
            return True
    return False


def _for_body_has_in_test_on_var(for_node: ast.For, loop_var: str) -> bool:
    for stmt in for_node.body:
        if isinstance(stmt, ast.If) and _compare_with_in_on_var(stmt.test, loop_var):
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
            if not _for_body_has_in_test_on_var(node, node.target.id):
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
```

### Tests: how we know the MVP works

`tests/test_rules.py` runs the **real analyzer** on **real benchmark files**:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from greenlint.analyzer import analyze_file

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks"


@pytest.mark.parametrize(
    "eco",
    ["eco1", "eco2", "eco3", "eco4"],
)
def test_bad_files_have_warnings(eco: str) -> None:
    path = BENCH / eco / "bad.py"
    diags = analyze_file(path)
    codes = {d.code for d in diags}
    assert eco.upper() in codes


@pytest.mark.parametrize(
    "eco",
    ["eco1", "eco2", "eco3", "eco4"],
)
def test_good_files_clean(eco: str) -> None:
    path = BENCH / eco / "good.py"
    diags = analyze_file(path)
    assert not diags, f"expected no diagnostics, got: {diags!r}"


def test_green_score_helpers() -> None:
    from greenlint.scoring import green_score

    assert green_score(0) == 10
    assert green_score(1) == 9
    assert green_score(15) == 0
```

---

## Requirements

- **Python 3.10+** (see `pyproject.toml`).

---

## Installation

From the directory that contains this `README.md` and `pyproject.toml`, it is recommended to use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -e .
```

That installs the package in **editable** mode and registers the **`greenlint`** console script.

To install development dependencies (for running tests):

```bash
pip install -e ".[dev]"
```

### If you see `ModuleNotFoundError: No module named 'greenlint'`

That almost always means the interpreter running the `greenlint` script is **not** the same environment where the package was installed.

1. **Activate the venv** you used for `pip install`, then reinstall cleanly from the folder that contains `pyproject.toml` and the `greenlint/` package:

   ```bash
   cd /path/to/SustainableSE2
   source .venv/bin/activate
   pip uninstall greenlint -y
   pip install -e .
   ```

2. **Check which `greenlint` runs** — it should live inside `.venv/bin`:

   ```bash
   which greenlint
   ```

   If it points somewhere else (e.g. another project or an old install), use the venv’s binary explicitly:

   ```bash
   .venv/bin/greenlint benchmarks/eco3/bad.py
   ```

3. **Run via Python** (uses whatever `python` is on your PATH, usually the venv’s after `activate`):

   ```bash
   python -m greenlint benchmarks/eco3/bad.py
   ```

4. **Quick sanity check**:

   ```bash
   python -c "import greenlint; print(greenlint.__file__)"
   ```

   If that fails, the package is not installed for that `python`.

This project builds with **Hatchling** (`pyproject.toml`); after changing the build backend or layout, run `pip install -e .` again.

---

## How to run GreenLint

Give a file or directory as the only positional argument:

```bash
greenlint path/to/something.py
greenlint path/to/package/
greenlint benchmarks/eco3/bad.py
```

Or, after install (especially if a stale `greenlint` script is on your PATH):

```bash
python -m greenlint path/to/something.py
```

**Example session** (output is illustrative; line numbers depend on the file):

```text
/Users/you/project/benchmarks/eco3/bad.py:3 ECO3 String concatenation in loop. Suggestion: use ''.join(...).
Green Score: 9
```

---

## Output format

Every warning is printed on **stdout** as a **single line** in this form:

```text
<absolute-path>:<line> <CODE> <message> Suggestion: <suggestion>
```

- **`absolute-path`**: resolved path of the file.
- **`line`**: 1-based line number in the source file (from the AST).
- **`CODE`**: one of `ECO1`, `ECO2`, `ECO3`, `ECO4`.
- **`message`** and **`suggestion`**: human-readable strings defined in each rule module.

After all warnings for a given file, GreenLint prints:

```text
Green Score: <integer>
```

---

## Green Score

For each successfully parsed file:

- The score **starts at 10**.
- **Subtract 1** for **each** warning in that file.
- The score **never goes below 0**.

Examples:

- 0 warnings → **10**
- 1 warning → **9**
- 12 warnings → **0** (10 − 12, floored at 0)

The score is **per file**. Scanning multiple files produces **multiple** `Green Score:` lines, one after each file’s warnings.

---

## The four rules (full detail with examples)

### ECO1 — `range(len(...))` loop with indexing

**Intent:** Iterating with `range(len(seq))` and then indexing `seq[i]` is a common pattern that avoids direct iteration. Often you want `for item in seq` or `enumerate(seq)`.

**What GreenLint detects**

- A `for` loop whose iterable is exactly **`range(len(some_name))`** (with no extra `range` arguments).
- The loop target is a **simple variable** (single `Name`, e.g. `i`).
- The expression passed to `len` is a **simple name** (e.g. `lst`), not `len(self.items)` or other expressions.
- The loop body (including nested statements inside the body) contains a **subscript** of the form **`that_same_name[index_var]`** where **`index_var`** is the loop variable.

**Example that triggers ECO1**

```python
lst = [1, 2, 3]
for i in range(len(lst)):
    x = lst[i]
    print(x)
```

**Example of a preferred style**

```python
lst = [1, 2, 3]
for item in lst:
    print(item)
```

Or, when you need the index:

```python
lst = [1, 2, 3]
for i, item in enumerate(lst):
    print(i, item)
```

**Diagnostic text (as implemented)**

- **Message:** `range(len(...)) loop with indexing.`
- **Suggestion:**

```text
use `for item in lst` or `enumerate()`.
```

**Limitations:** If `len` is applied to something that is not a bare name (for example an attribute or call), ECO1 does not match that `len` expression, even if the pattern is similar in spirit.

---

### ECO2 — building a list with repeated `.append()` in a loop

**Intent:** Appending to a list inside a loop when every iteration only appends can often be expressed as a **list comprehension**, which is typically clearer and can be faster.

**What GreenLint detects**

- In a **module**, **function**, **async function**, or **class** body, a statement of the form **`name = []`** (assignment to a name with an **empty list** literal).
- The **very next statement** must be a **`for`** loop.
- Every statement in that **`for`** body must be an **expression statement** that is a **call** to **`name.append(...)`** (the object receiving `.append` must be exactly that name).

**Example that triggers ECO2**

```python
items = [1, 2, 3]
result = []
for x in items:
    result.append(x * 2)
```

**Example of a preferred style**

```python
items = [1, 2, 3]
result = [x * 2 for x in items]
```

**Diagnostic text (as implemented)**

- **Message:** `Building a list with .append() in a loop.`
- **Suggestion:** `use a list comprehension.`

**Limitations:** The empty-list assignment must be **immediately before** the `for` loop. If there is any other statement in between (even a comment-only line is fine, but not another statement), the pattern is not matched. The rule also requires that **all** body statements are `.append` calls; if the loop mixes appends with other work, it will not report ECO2.

---

### ECO3 — string concatenation with `+=` inside a loop

**Intent:** Repeated `str += piece` in a loop can cause many intermediate string objects. Joining once at the end is the usual idiom.

**What GreenLint detects**

- Same statement-block contexts as ECO2 (module, function, async function, class body).
- The statement before a **`for`** loop must assign **`""`** to a **name** using a **`Constant`** (empty string).
- The **`for`** loop body must contain at least one **`+=` augmented assignment** (`AugAssign`) with **`+`** on **that same name**.

**Example that triggers ECO3**

```python
items = [1, 2, 3]
s = ""
for x in items:
    s += str(x)
```

**Example of a preferred style**

```python
items = [1, 2, 3]
s = "".join(str(x) for x in items)
```

**Diagnostic text (as implemented)**

- **Message:** `String concatenation in loop.`
- **Suggestion:** `use ''.join(...).`

**Limitations:** Only `+=` is considered, not `s = s + ...`. The empty string must come from the **immediate previous** assignment, same as ECO2’s pairing rule.

---

### ECO4 — membership test with `in` inside the loop body

**Intent:** Testing **`x in container`** where `container` is a **list** or other structure that implies **linear** membership cost, **inside** a loop over other data, can become **O(n × m)**. Using a **set** for membership can reduce expected cost when membership is repeated.

**What GreenLint detects**

- A `for` loop whose target is a **simple name** (the “loop variable”).
- On the **first level** of the `for` body, there is an **`if`** whose **test** is a **`Compare`** node where:
  - the **left** side is **exactly that loop variable**, and
  - one of the operators is **`in`**, and
  - for that **`in`**, the **right-hand side** is **not** considered “set-like” by GreenLint.

**Right-hand sides that do not trigger ECO4**

- A **set literal**: `{ ... }`
- A call to **`set(...)`** where the callable is the bare name **`set`**

**Example that triggers ECO4**

```python
values = [1, 2, 3]
for x in values:
    if x in [2]:
        print(x)
```

**Example that does not trigger ECO4** (set literal on the right of `in`)

```python
values = [1, 2, 3]
for x in values:
    if x in {2}:
        print(x)
```

**Diagnostic text (as implemented)**

- **Message:** `Membership check against a sequence inside a loop.`
- **Suggestion:** `use a set for membership tests.`

**Limitations:** GreenLint does **not** perform type inference. If you write `if x in my_set` where `my_set` is a **variable**, GreenLint **cannot** know that it is a set; it may still warn because the comparand is a name. For the course benchmarks, the “good” example uses **`{2}`** so the tool can see a set literal. Nested `if` statements (not direct children of the `for` body) are **not** searched for this MVP.

---

## Repository layout

```text
project2/SustainableSE2/
  pyproject.toml          # package metadata, greenlint entry point, pytest config
  README.md               # this file
  .gitignore              # venv, caches, build artifacts
  greenlint/
    __init__.py
    cli.py                # argument parsing, file discovery, printing, exit codes
    analyzer.py           # parse source, run all rules, sort diagnostics
    diagnostics.py        # Diagnostic dataclass and line formatting
    scoring.py            # Green Score arithmetic
    rules/
      __init__.py         # ALL_RULES list
      base.py             # abstract BaseRule
      eco1.py             # ECO1
      eco2.py             # ECO2
      eco3.py             # ECO3
      eco4.py             # ECO4
  benchmarks/
    eco1/bad.py good.py
    eco2/bad.py good.py
    eco3/bad.py good.py
    eco4/bad.py good.py
  tests/
    test_rules.py         # pytest: bad must fire; good must be clean
```

---

## Benchmarks

Under `benchmarks/ecoN/`, each `bad.py` is written to trigger rule **ECON** once (in isolation), and each `good.py` is written so that **no** rule fires. They are used both as **documentation** and as **fixtures** for tests.

---

## Tests

After installing with the `dev` extra:

```bash
pytest
```

Tests assert:

- Each **`bad.py`** produces at least one diagnostic whose **code** is the expected **`ECO`N**.
- Each **`good.py`** produces **no** diagnostics at all (so unrelated rules cannot slip silently).

There is also a small test that the **Green Score** helper returns **10**, **9**, and **0** for representative warning counts. (The full test source is pasted under **How we implement it** above.)

---

## Honest scope statement

GreenLint is a **teaching** tool. It encodes **four** brittle string-and-AST patterns. It will **miss** real inefficiencies that do not match those patterns, and it may **rarely** disagree with human judgment. Treat it as a **starting point** for discussing algorithms and data structures, not as a complete quality or energy gate for production software.
