from __future__ import annotations

import argparse
import sys
from pathlib import Path

from greenlint.analyzer import analyze_file
from greenlint.estimates import load_summary
from greenlint.scoring import green_score


def _collect_py_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="greenlint",
        description="GreenLint — AST energy-style anti-patterns with benchmark-backed estimates",
    )
    parser.add_argument("path", type=Path, help="File or directory to scan")
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Path to experiments/results/summary.json (default: bundled / repo copy)",
    )
    args = parser.parse_args(argv)
    root: Path = args.path
    if not root.exists():
        print(f"greenlint: path not found: {root}", file=sys.stderr)
        return 2

    files = _collect_py_files(root)
    if not files:
        print("greenlint: no Python files found", file=sys.stderr)
        return 1

    summary = load_summary(args.summary)
    exit_code = 0
    total_warnings = 0

    for path in files:
        try:
            diagnostics = analyze_file(path, summary_path=args.summary)
        except SyntaxError as exc:
            print(f"greenlint: {path}: syntax error: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        if diagnostics:
            exit_code = 1
        total_warnings += len(diagnostics)
        display = str(path.resolve())
        for d in diagnostics:
            print(d.format_line(display))
        score = green_score(diagnostics, summary)
        print(f"Warnings: {len(diagnostics)}")
        print(f"Green Score: {score}")

    if len(files) > 1:
        print(f"Total warnings: {total_warnings}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
