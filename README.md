# GreenLint

Small **course project**: walk the **AST**, flag a few **wasteful patterns**, attach rough **Joules / CO₂** numbers from **`experiments/results/summary.json`**, print a **0–10 score**. Not real power measurement.

**Needs:** Python **3.10+**, repo root = folder with **`pyproject.toml`** (call it **`REPO`** below).

---

## Install

**Option A — virtualenv (keeps deps in `.venv/`):**

```bash
cd REPO
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
pip install -e ".[dev]"            # pytest
pip install -e ".[benchmarks]"    # pandas + codecarbon; only for experiments/
```

**Option B — no venv:** same `pip install` lines with **`python3 -m pip`**, skip `venv` / `activate`.

---

## Run

From **`REPO`** (with venv activated if you use one):

```bash
greenlint benchmarks/eco1/bad.py
greenlint benchmarks/
pytest
env -u GREENLINT_CODECARBON python experiments/run_benchmark.py --repeats 15
```

Last line rebuilds **`experiments/results/summary.json`** (can take a few minutes; ECO6 is heavy). **`raw_runs.csv`** is local-only (gitignored). Use **`env -u GREENLINT_CODECARBON`** so benchmarks use simple **time → proxy energy** instead of CodeCarbon hardware stuff that breaks in some terminals.

Optional: set **`GREENLINT_PROXY_J_PER_S`** / **`GREENLINT_PROXY_CO2_KG_PER_S`** to scale numbers in the JSON without changing timings.

---

## Layout

| Path | Role |
|------|------|
| `greenlint/rules.py` | ECO1–ECO7 checks |
| `greenlint/analyzer.py` | parse, run rules, load `summary.json`, scores |
| `greenlint/cli.py` | CLI |
| `greenlint/diagnostics.py` | one small `Diagnostic` type |
| `benchmarks/eco1` … `eco7` | `bad.py` / `good.py` pairs (large on purpose) |
| `experiments/` | `run_benchmark.py`, `benchmark_runner.py`, `codecarbon_utils.py`, `results/summary.json` |
| `tests/` | pytest |

---

## Rules

| Code | Idea |
|------|------|
| ECO1 | `range(len(x))` + index |
| ECO2 | build list with `.append` in a loop |
| ECO3 | `s += ...` on strings in a loop |
| ECO4 | `x in` something slow inside a loop |
| ECO5 | unused “heavy” import at top level |
| ECO6 | `pandas` `iterrows()` |
| ECO7 | `pandas` `.apply` where vectorized code works |

**Score:** starts at **10**, subtract each warning’s **weight** from `summary.json` (default **1** if missing), clamp to **0–10**.

---

## Scope

Coursework demo: static checks + offline benchmarks give **ballpark** hints, not accounting-grade CO₂.
