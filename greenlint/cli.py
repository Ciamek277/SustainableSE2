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
