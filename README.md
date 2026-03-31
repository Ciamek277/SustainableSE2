# GreenLint

GreenLint is a course project CLI that scans Python files with `ast` and reports 7 energy-style anti-patterns (`ECO1`...`ECO7`).

It also prints:
- estimated Joules / CO2 per warning (loaded from `experiments/results/summary.json`)
- a Green Score from 0 to 10

These energy values are benchmark-derived estimates, not direct hardware measurements.

## What it does

- scans a Python file or directory and reports ECO1..ECO7 warnings
- shows line number, rule code, short suggestion, and estimated savings
- computes a simple Green Score (0-10) from benchmark-derived rule weights
- lets you regenerate benchmark summary data (`summary.json`) from `bad.py`/`good.py` pairs

## Example output

```text
/.../benchmarks/eco1/bad.py:5 ECO1 range(len(...)) loop with indexing. Suggestion: use `for item in lst` or `enumerate()`. Estimated saving: 0.27 J, 0.000 g CO2e
Warnings: 1
Green Score: 9
```

## Requirements

- Python 3.10+
- Run commands from the folder that contains `pyproject.toml` (examples below use `/path/to/SustainableSE2`)

## Step-by-step (recommended)

### 1) Create and activate a virtual environment

```bash
cd /path/to/SustainableSE2
python3 -m venv .venv
source .venv/bin/activate
```

Windows:
- `cmd`: `.venv\Scripts\activate.bat`
- PowerShell: `.venv\Scripts\Activate.ps1`

### 2) Install dependencies

```bash
pip install -e ".[dev,benchmarks]"
```

What this installs:
- package + CLI (`greenlint`)
- test tools (`pytest`)
- benchmark deps (`pandas`, `codecarbon`)

### 3) Run tests

```bash
pytest
```

Expected: all tests pass.

### 4) Run the linter

Single file with known warning:

```bash
greenlint benchmarks/eco1/bad.py
```

Expected:
- one `ECO1` warning
- `Warnings: 1`
- non-zero exit code (`1`)

Single file without warning:

```bash
greenlint benchmarks/eco1/good.py
```

Expected:
- `Warnings: 0`
- `Green Score: 10`
- exit code `0`

Scan all benchmark files:

```bash
greenlint benchmarks/
```

### 5) Regenerate benchmark summary

```bash
env -u GREENLINT_CODECARBON python experiments/run_benchmark.py --repeats 15
```

Expected output includes:

```text
Wrote .../experiments/results/summary.json
```

This command updates:
- `experiments/results/summary.json` (commit this if you want updated baseline values)
- `experiments/results/raw_runs.csv` (local file, gitignored)

`--repeats 15` can take a few minutes (ECO6 is the slowest benchmark).

## Optional flags/env vars

- `greenlint --summary experiments/results/summary.json <path>`
  - use a specific summary file
- `GREENLINT_PROXY_J_PER_S`
- `GREENLINT_PROXY_CO2_KG_PER_S`
  - scale proxy values used in benchmark-generated estimates

## Minimal workflow for teammates

```bash
cd /path/to/SustainableSE2
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,benchmarks]"
pytest
greenlint benchmarks/
env -u GREENLINT_CODECARBON python experiments/run_benchmark.py --repeats 15
```

## Project structure

- `greenlint/rules.py` - ECO1..ECO7 checks
- `greenlint/analyzer.py` - run rules, load summary, scoring helpers
- `greenlint/cli.py` - command line entrypoint
- `benchmarks/eco1`...`eco7` - `bad.py` / `good.py` benchmark pairs
- `experiments/` - benchmark runner + summary generation
- `tests/` - pytest suite

## Limitations

- energy values are proxy estimates based on benchmark runtime, not direct hardware power readings
- results vary by machine/load; use them for relative comparison, not absolute accounting
- rules are intentionally simple for course scope, so some real-world edge cases are out of scope

## Scope

This is a coursework tool: static pattern detection + offline benchmark estimates. It is not intended to be production carbon accounting.
