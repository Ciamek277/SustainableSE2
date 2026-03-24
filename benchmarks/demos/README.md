# Optional “large” demos (manual / CodeCarbon)

The small `ecoN/bad.py` / `good.py` files are for **fast** tests and quick runs.  
These scripts use **bigger workloads** so **bad vs good** differences show up more clearly in **timing** or **CodeCarbon** when you run them yourself (they are **not** used by `pytest`).

Example (from repo root, with pandas installed for ECO6/7 demos):

```bash
time python benchmarks/demos/eco3_string_concat_bad.py
time python benchmarks/demos/eco3_string_concat_good.py
```

Expect the **good** variant to finish faster for large `N`.
