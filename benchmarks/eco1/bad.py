# Large workload so bad vs good separate in duration-based proxy metrics.
N = 400_000
lst = list(range(N))
acc = 0
for i in range(len(lst)):
    acc += lst[i]
print(acc)
