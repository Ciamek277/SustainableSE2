# Heavy stdlib import unused at module level (lazy import preferred when needed).
# The import adds real load-time / memory cost on top of the workload below—intentional
# so “bad” runs reflect bloated modules and we still measure the same work as good.py.
import multiprocessing

N = 1_200_000
acc = 0
for i in range(N):
    acc += i
print(acc)
