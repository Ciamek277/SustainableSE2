# GreenLint

CLI that finds **energy-related Python anti-patterns** with the **`ast`** module. Savings numbers (**Joules**, **CO₂e**, **weights**) come from **`experiments/results/summary.json`**, which you can regenerate by running benchmarks (`bad.py` vs `good.py` per rule). This is **not** a hardware power meter.

---

## What you need

- **Python 3.10+**
- A clone of this repo; below, **`REPO`** means the folder that contains `pyproject.toml` (e.g. `.../SustainableSE2`).

---

## 1. Install (do this once per machine)

Open a terminal and run:

```bash
cd REPO
python3 -m venv .venv
```

Activate the venv:

- **macOS / Linux:** `source .venv/bin/activate`
- **Windows (cmd):** `.venv\Scripts\activate.bat`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

Install the package in editable mode:

```bash
pip install -e .
```

That installs the **`greenlint`** command (see `pyproject.toml` → `[project.scripts]`).

**Optional:**

```bash
pip install -e ".[dev]"        # pytest (for running tests)
pip install -e ".[benchmarks]" # pandas + codecarbon (needed to run experiments/benchmarks)
```

---

## 2. Run the linter (`greenlint`)

Always run these **from `REPO`** (or use absolute paths). The last argument is **one** path: a **`.py` file** or a **directory** (all `*.py` files under it are scanned).

### Examples that work in this repo

Lint a single benchmark file (expect warnings on `bad.py`):

```bash
cd REPO
source .venv/bin/activate   # if not already active

greenlint benchmarks/eco1/bad.py
greenlint benchmarks/eco1/good.py
```

Lint all benchmarks:

```bash
greenlint benchmarks/
```

Use an explicit summary file (same defaults as the copy next to the package when installed editable):

```bash
greenlint --summary experiments/results/summary.json benchmarks/eco3/bad.py
```

**`--summary PATH`** — JSON file with per-rule `delta_joules_median`, `weight`, etc. If you omit it, GreenLint loads **`experiments/results/summary.json`** from the installed package layout (works when you run from the repo after `pip install -e .`).

**Exit code:** `0` = no issues, `1` = at least one warning or no Python files, `2` = path does not exist.

---

## 3. Run tests

```bash
cd REPO
source .venv/bin/activate
pip install -e ".[dev]"   # once, if you have not already
pytest
```

---

## 4. Regenerate `experiments/results/summary.json`

Benchmarks execute each `benchmarks/ecoN/bad.py` and `good.py` many times and write:

- **`experiments/results/summary.json`** — medians and weights (safe to commit)
- **`experiments/results/raw_runs.csv`** — raw rows (**gitignored**; do not commit)

Requires benchmark dependencies:

```bash
cd REPO
source .venv/bin/activate
pip install -e ".[benchmarks]"
```

Recommended: clear CodeCarbon hardware mode so the default **wall-clock proxy** is used (avoids `powermetrics` / `sudo` issues in IDEs):

```bash
env -u GREENLINT_CODECARBON python experiments/run_benchmark.py --repeats 15
```

- Omit **`env -u ...`** only if you intentionally set `GREENLINT_CODECARBON=1` (optional; may fall back to the same proxy).

ECO6 is slow; a full run can take **several minutes**.

**Typical order:** run **`pytest`**, then **`run_benchmark.py`** if you want fresh numbers.

---

## Green Score

- Starts at **10**.
- Each warning subtracts that rule’s **`weight`** from `summary.json` (default **1.0** if missing).
- Printed score is an integer in **[0, 10]**.

---

## Rules (ECO1–ECO7)

| Code | Pattern |
|------|---------|
| ECO1 | `for i in range(len(x)): x[i]` |
| ECO2 | `list = []; for: list.append(...)` |
| ECO3 | `s += ...` on strings in a loop |
| ECO4 | `x in` a slow container in a loop; prefer **set** |
| ECO5 | Unused **heavy** top-level import |
| ECO6 | `pandas` `iterrows()` |
| ECO7 | `pandas` `.apply(...)` where vectorized ops suffice |

---

## Benchmark details (optional)

- **Proxy energy:** `experiments/codecarbon_utils.py` measures **duration** per run and maps it to J / CO₂ using factors recorded in `summary.json` (`proxy_joules_per_second`, etc.). Override with **`GREENLINT_PROXY_J_PER_S`** and **`GREENLINT_PROXY_CO2_KG_PER_S`** if you want different numeric scale.
- **`summary.json`** also has **`delta_duration_s_median`** per rule (often easiest to read).

---

## Repo layout

```
greenlint/                 # package (CLI, rules, estimates)
benchmarks/eco1..eco7/     # bad.py / good.py
experiments/               # run_benchmark.py, results/summary.json
tests/                     # pytest
benchmarks/demos/          # optional larger demos (see benchmarks/demos/README.md)
```

---

## Honest scope

Static analysis plus offline benchmarks give **rough** hints for coursework, not certified carbon accounting for production systems.
