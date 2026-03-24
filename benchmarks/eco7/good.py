import pandas as pd

N = 80_000
df = pd.DataFrame({"x": range(N)})
df["y"] = df["x"] * 2
print(int(df["y"].iloc[-1]))
