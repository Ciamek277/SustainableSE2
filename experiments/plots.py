import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors

with open("experiments/results/summary.json", "r") as f:
    data = json.load(f)

rules = list(data["rules"].keys())
delta_runtime = [data["rules"][rule]["delta_duration_s_median"] for rule in rules]

norm = mcolors.LogNorm(vmin=min(delta_runtime), vmax=max(delta_runtime))
colors = [cm.RdYlGn_r(norm(v)) for v in delta_runtime]

fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
fig.subplots_adjust(hspace=0.08, top=0.93, left=0.15)

ax_top.bar(rules, delta_runtime, color=colors)
ax_bottom.bar(rules, delta_runtime, color=colors)

ax_top.set_ylim(0.02, max(delta_runtime) * 1.12)
ax_bottom.set_ylim(0, 0.02)

ax_top.spines["bottom"].set_visible(False)
ax_bottom.spines["top"].set_visible(False)
ax_top.tick_params(bottom=False)

d = 0.008
kwargs = dict(transform=ax_top.transAxes, color="k", clip_on=False, linewidth=1)
ax_top.plot((-d, +d), (-d, +d), **kwargs)
ax_top.plot((1 - d, 1 + d), (-d, +d), **kwargs)
kwargs.update(transform=ax_bottom.transAxes)
ax_bottom.plot((-d, +d), (1 - d, 1 + d), **kwargs)
ax_bottom.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)

for i, (rule, value) in enumerate(zip(rules, delta_runtime)):
    if value >= 0.02:
        ax_top.text(i, value + max(delta_runtime) * 0.01, f"{value:.4f}",
                    ha="center", va="bottom", fontsize=8)
    else:
        ax_bottom.text(i, value + 0.0005, f"{value:.4f}",
                       ha="center", va="bottom", fontsize=8)

ax_bottom.set_xlabel("Rule")
fig.text(0.04, 0.5, "Median runtime difference (s)", va="center", rotation="vertical")
fig.suptitle("Median runtime difference between bad and good benchmark variants")

plt.savefig("experiments/results/rq1_runtime_delta.png", dpi=300, bbox_inches="tight")
plt.show()