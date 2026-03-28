import json
import matplotlib.pyplot as plt

with open("experiments/results/summary.json", "r") as f:
    data = json.load(f)

rules = list(data["rules"].keys())
delta_runtime = [data["rules"][rule]["delta_duration_s_median"] for rule in rules]

plt.figure(figsize=(8, 4.5))
bars = plt.bar(rules, delta_runtime)

plt.xlabel("Rule")
plt.ylabel("Median runtime difference (s)")
plt.title("Median runtime difference between bad and good benchmark variants")

plt.ylim(0, max(delta_runtime) * 1.12)

for bar, value in zip(bars, delta_runtime):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + max(delta_runtime) * 0.01,
        f"{value:.4f}",
        ha="center",
        va="bottom",
        fontsize=8
    )

plt.tight_layout()
plt.savefig("experiments/results/rq1_runtime_delta.png", dpi=300, bbox_inches="tight")
plt.show()