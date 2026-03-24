import pandas as pd

N = 100_000
df = pd.DataFrame({"a": range(N)})
print(int(df["a"].sum()))
