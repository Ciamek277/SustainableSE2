#!/usr/bin/env python3
"""Run all eco benchmarks with CodeCarbon (optional) and regenerate summary.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Run GreenLint benchmark suite (bad vs good per ECO).")
    p.add_argument("--repeats", type=int, default=30, help="Runs per variant (default 30)")
    args = p.parse_args()
    from experiments.benchmark_runner import run_all

    out = run_all(repeats=args.repeats)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
