"""ECO1 good: direct iteration — compare with eco1_range_len_bad.py."""

N = 100_000
lst = list(range(N))
acc = 0
for v in lst:
    acc += v
print(acc)
