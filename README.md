# GreenLint

**GreenLint** is a pip-installable CLI that flags common **energy-related** Python anti-patterns using the **`ast`** module. It does **not** read hardware sensors from your source code. Per-rule **Joules** and **CO₂e** “savings” come from **`experiments/results/summary.json`**, produced by comparing **`benchmarks/eco1`–`eco7`** `bad.py` vs `good.py` runs (same kind of work, bad pattern vs fixed pattern).

## Install

```bash
cd project2/SustainableSE2   # or your clone path
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

Optional extras:

```bash
pip install -e ".[dev]"        # pytest, etc.
pip install -e ".[benchmarks]" # CodeCarbon (only if you enable it; see below)
```

## Run the CLI

```bash
greenlint path/to/file_or_dir.py
greenlint benchmarks/
greenlint --summary experiments/results/summary.json myapp/
```

Each finding can show estimated savings from `summary.json`. With multiple files, a final line prints **`Total warnings: N`**.

## Green Score

- Starts at **10**.
- Each warning subtracts that rule’s **`weight`** from `summary.json` (default **1.0** if missing).
- Result is truncated to an integer in **[0, 10]**.

## Rules (ECO1–ECO7)

| Code | Pattern |
|------|---------|
| ECO1 | `for i in range(len(x)): x[i]` |
| ECO2 | `list = []; for: list.append(...)` |
| ECO3 | `s += ...` on strings in a loop |
| ECO4 | `x in` a slow container inside a loop (e.g. list); prefer **set** |
| ECO5 | Unused **heavy** top-level import |
| ECO6 | `pandas` `iterrows()` |
| ECO7 | `pandas` `.apply(...)` where vectorized ops suffice |

## Benchmarks & `summary.json`

For each `benchmarks/ecoN/`, **`bad.py`** exercises the anti-pattern and **`good.py`** the preferred style on a **large workload** so wall-clock differences show up in aggregates.

**Regenerate** `experiments/results/summary.json` (and `raw_runs.csv`):

```bash
env -u GREENLINT_CODECARBON python experiments/run_benchmark.py --repeats 15
```

- Default **`--repeats`** in the script is **30**; **15** is a common choice. ECO6 (`iterrows` on a large frame) dominates runtime; a full run can take **several minutes** on a laptop.

**Suggested workflow** (tests first, then metrics):

```bash
pytest
env -u GREENLINT_CODECARBON python experiments/run_benchmark.py --repeats 15
```

### How numbers are produced

By default, `experiments/codecarbon_utils.py` runs each script once per repeat, measures **wall-clock time**, and maps it to **proxy** Joules and CO₂ (not a power meter). Values are **category-level** hints for coursework, not certified carbon accounting.

`summary.json` includes, per rule:

- **`delta_joules_median`**, **`delta_co2_grams_median`**, **`weight`** (normalized across rules)
- **`delta_duration_s_median`**, **`median_duration_bad_s`**, **`median_duration_good_s`** (often easiest to interpret)
- Top-level **`proxy_joules_per_second`** and **`proxy_co2_kg_per_second`** (defaults **25** and **5×10⁻⁷**)

Override the proxy scale (larger numbers in the file; **bad vs good ratios** unchanged for the same machine):

```bash
export GREENLINT_PROXY_J_PER_S=40
export GREENLINT_PROXY_CO2_KG_PER_S=8e-7
```

### Optional CodeCarbon

In a **normal terminal** (not all IDE sandboxes), you can try:

```bash
export GREENLINT_CODECARBON=1
python experiments/run_benchmark.py --repeats 15
```

If `OfflineEmissionsTracker` fails, the same duration proxy is used.

### If you see `BlockingIOError` or `sudo: unable to allocate pty`

That usually comes from CodeCarbon’s **hardware** path (`powermetrics` / `sudo`). **Unset** `GREENLINT_CODECARBON` (or use `env -u GREENLINT_CODECARBON` as above) so benchmarks use the default time-based proxy.

### Git / teammates

Commit **`greenlint/`**, **`tests/`**, **`benchmarks/`**, **`experiments/*.py`**, **`pyproject.toml`**, and a baseline **`experiments/results/summary.json`**. Do **not** commit **`.venv/`** or **`experiments/results/raw_runs.csv`** (see `.gitignore`).

## Repo layout

```
greenlint/                 # package: CLI, analyzer, rules, estimates
benchmarks/eco1..eco7/     # bad.py / good.py pairs
experiments/               # benchmark runner, proxy helpers, results/
tests/                     # pytest
```

Optional larger scripts: `benchmarks/demos/` (see `benchmarks/demos/README.md`).

## Tests

```bash
pytest
```

- **Rules / CLI:** `tests/test_eco*.py`, `test_cli.py`, `test_scoring.py`
- **AST edge cases:** `tests/test_advanced_patterns.py`
- **Estimates:** `tests/test_energy_estimates.py`

## Honest scope

Static analysis plus offline benchmarks give **rough** savings hints. **Do not** treat outputs as production-grade carbon accounting.
