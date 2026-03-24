"""ECO3 bad: O(n²) string concatenation — use for profiling only (not in pytest)."""

N = 30_000
s = ""
for i in range(N):
    s += str(i % 10)
print(len(s))
