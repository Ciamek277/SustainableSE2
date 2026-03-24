import pandas as pd

N = 100_000
df = pd.DataFrame({"a": range(N)})
s = 0
for _, row in df.iterrows():
    s += int(row["a"])
print(s)
