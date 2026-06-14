#!/usr/bin/env python3
"""Figure 1 — the layered pre-flight pipeline (regenerated 2026-06-06, v2).

v2: rebalanced left (gate cascade) vs right (routing-verdict column) so the right
side is no longer compressed/overlapping; verdict boxes widened and spaced; the
"routing verdict" label sits clear above them; forward fan-out arrows. Run:
  python fig1_pipeline.py   ->  fig1_pipeline.pdf
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

fig, ax = plt.subplots(figsize=(8.0, 3.0))
ax.set_xlim(0, 100)
ax.set_ylim(0, 44)
ax.axis("off")

INK = "#222222"

def box(x, y, w, h, text, fc="#f2f2f2", ec="#555555", fs=8.5, tc=INK, lw=1.1):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.6",
        linewidth=lw, edgecolor=ec, facecolor=fc, mutation_aspect=0.65))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, zorder=5)

def arrow(x0, y0, x1, y1, color="#555555", lw=1.3):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                 mutation_scale=11, linewidth=lw, color=color,
                 shrinkA=0, shrinkB=0))

YC, BH = 12.0, 12.0          # gate-row bottom, gate height (centre = 18)
ymid = YC + BH / 2

# --- input + 4 gates across the left/centre (x: 1 .. 81) ---
box(1.0, YC, 13.5, BH, "Structure /\nendpoints /\nband", fc="#eaeaea")
gx, gw, gap = 17.5, 14.0, 2.5
labels = ["electron_\nparity\n(M0, pre-DFT)", "spin_\ncollapse",
          "endpoint\nΔM gate", "in-band\nΔM gate"]
xs = [gx + i * (gw + gap) for i in range(4)]
for x, lab in zip(xs, labels):
    box(x, YC, gw, BH, lab, fc="#f2f2f2")

# cascade arrows (input -> g1 -> ... -> g4)
arrow(14.5, ymid, xs[0], ymid)
for i in range(3):
    arrow(xs[i] + gw, ymid, xs[i + 1], ymid)

ax.text((xs[0] + xs[-1] + gw) / 2, 27.5,
        "pre-flight gate cascade  (before the expensive NEB)",
        ha="center", va="center", fontsize=8, style="italic", color="#666666")

# --- routing-verdict column (right: x 86 .. 99) ---
vx, vw, vh = 86.0, 13.0, 8.0
last_right = xs[-1] + gw            # right edge of in-band gate (= 81)
verdicts = [
    (30.0, "NO-GO_\nSINGLE_SHEET", "#c0392b"),
    (16.0, "REVIEW", "#e67e22"),
    (2.0,  "GO → NEB", "#2980b9"),
]
for vy, lab, col in verdicts:
    box(vx, vy, vw, vh, lab, fc="white", ec=col, tc=col, fs=8, lw=1.5)
    arrow(last_right, ymid, vx, vy + vh / 2, color="#aaaaaa", lw=1.0)

ax.text(vx + vw / 2, 42.5, "routing verdict", ha="center", va="center",
        fontsize=8, style="italic", color="#666666")

fig.savefig("fig1_pipeline.pdf", bbox_inches="tight", pad_inches=0.2)
print("wrote fig1_pipeline.pdf")
