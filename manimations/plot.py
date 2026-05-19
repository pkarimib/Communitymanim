import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update(
    {
        "text.usetex": True,
        "text.latex.preamble": r"\usepackage{times}",
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "font.family": "serif",
        "font.serif": "Times",
        "axes.labelsize": 12,
        "axes.titlesize": 12,
        "figure.labelsize": 12,
        "figure.titlesize": 12,
        "hatch.linewidth": 0.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42
    }
)

# Data extracted from HRA-Cloud.png. x-grid is 4:0.5:8; AIScheduler is
# missing x=4.5 (per the original code).
x_full = np.arange(4.0, 8.001, 0.5)
x_ais  = np.array([4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0])

# Visible markers extracted via 2D-density localization. Hidden markers
# (where AIS or LLQ stacks on top) are filled with values that fall within
# a marker-width of the visible top marker, since "hidden" means pixel overlap.
results = {
    "rr":  (x_full, [1.010, 1.120, 1.339, 1.949, 2.742, 5.108, 8.214, 15.342, 22.545]),
    "llq": (x_full, [1.020, 1.048, 1.120, 1.260, 1.602, 2.796, 6.992, 14.604, 21.469]),
    "ais": (x_ais,  [1.002,        1.116, 1.160, 1.256, 1.487, 1.944, 3.143,  4.803]),
}
pretty_lbl = {"rr": "Round Robin", "llq": "LLQ", "ais": "Glia"}
colors     = {"rr": "C3",          "llq": "C0",  "ais": "C2"}
test_names = ["rr", "llq", "ais"]

fsize = (4, 3.5)
ftitle = "Cloud"

fig, ax = plt.subplots(1, 1, figsize=fsize)
for name in test_names:
    xs, ys = results[name]
    ax.plot(
        xs,
        ys,
        marker="s",
        markersize=3,
        label=pretty_lbl[name],
        color=colors[name],
    )

ax.set_xticks([4, 5, 6, 7, 8])
ax.set_ylim(-0.07, 23.62)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.plot(1, 0, ">k", transform=ax.transAxes, clip_on=False)
ax.plot(0, 1, "^k", transform=ax.transAxes, clip_on=False)
ax.grid(True, alpha=0.3)
ax.set_xlabel("Queries Per Second")
ax.set_ylabel("Average Slowdown")
ax.set_title(ftitle)
ax.legend()

ax.annotate(
    "",
    xy=(4.75, 0.25),
    xytext=(4.75, 0.65),
    arrowprops=dict(arrowstyle="->", facecolor="black", lw=1.5),
    xycoords=("data", "axes fraction"),
    textcoords=("data", "axes fraction"),
)
ax.text(
    4.85,
    0.48,
    "Better",
    ha="left",
    va="center",
    fontsize=11,
    transform=ax.get_xaxis_transform(),
)

fig.tight_layout()
fig.savefig("recreated.pdf", dpi=300, transparent=False)
print("saved recreated.png")
