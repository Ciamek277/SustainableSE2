candidates = set(range(25_000))
hits = 0
for x in range(10_000):
    if x in candidates:
        hits += 1
print(hits)
