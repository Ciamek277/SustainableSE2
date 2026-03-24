from __future__ import annotations

import argparse
import sys
from pathlib import Path

from greenlint.analyzer import analyze_file, green_score, load_summary


def _py_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="greenlint")
    p.add_argument("path", type=Path, help="Python file or directory")
    p.add_argument("--summary", type=Path, default=None, help="Path to summary.json")
    args = p.parse_args(argv)
    if not args.path.exists():
        print(f"greenlint: path not found: {args.path}", file=sys.stderr)
        return 2

    files = _py_files(args.path)
    if not files:
        print("greenlint: no Python files found", file=sys.stderr)
        return 1

    summary = load_summary(args.summary)
    exit_code = 0
    total = 0

    for path in files:
        try:
            diagnostics = analyze_file(path, summary_path=args.summary)
        except SyntaxError as exc:
            print(f"greenlint: {path}: syntax error: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        if diagnostics:
            exit_code = 1
        total += len(diagnostics)
        display = str(path.resolve())
        for d in diagnostics:
            print(d.format_line(display))
        print(f"Warnings: {len(diagnostics)}")
        print(f"Green Score: {green_score(diagnostics, summary)}")

    if len(files) > 1:
        print(f"Total warnings: {total}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
