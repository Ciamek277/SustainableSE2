"""ECO1 bad: range(len) + index — larger N for clearer timing vs good demo."""

N = 100_000
lst = list(range(N))
acc = 0
for i in range(len(lst)):
    acc += lst[i]
print(acc)
