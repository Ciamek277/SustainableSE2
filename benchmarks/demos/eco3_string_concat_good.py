"""ECO3 good: single join — compare runtime vs eco3_string_concat_bad.py."""

N = 30_000
parts = [str(i % 10) for i in range(N)]
s = "".join(parts)
print(len(s))
