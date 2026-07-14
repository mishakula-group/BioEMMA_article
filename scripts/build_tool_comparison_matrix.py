from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "tool_comparison"
OUTPUT_PATH = OUTPUT_DIR / "tool_comparison_matrix.png"

TOOLS = [
    "CytoSEED",
    "CAVE",
    "Grohar",
    "Fluxer",
    "MetExplore V2",
    "FLUXestimator",
    "ModelExplorer",
    "SAMMI",
    "IMFLer",
    "Escher",
    "NAViFluX",
    "BioEMMA",
]

FEATURES = [
    "Standard model format input\n(SBML / JSON)",
    "Pathway / subsystem-level\nvisualization",
    "Flux data overlay",
    "Interactive browser-based\nvisualization",
    "Publication-ready\nvector export",
    "Offline / local execution",
    "Programmatic access\n(Python API)",
    "Automatic map generation",
    "Canonical pathway-consistent\nlayout",
    "KEGG-guided automatic\nlayout synthesis",
    "Native Escher-compatible\nJSON output",
]

# 0 = no support, 1 = full support, 2 = limited support.
MATRIX = np.array(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
        [0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
        [0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1],
        [0, 0, 0, 0, 2, 1, 0, 1, 0, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
    ]
)

FULL = "#68B740"
LIMITED = "#F3DE3D"
NONE = "#FFFFFF"
GRID = "#CCCCCC"
BIOEMMA_COLUMN = "#E8F4F8"
BIOEMMA_HEADER = "#68B740"


def main() -> None:
    n_tools = len(TOOLS)
    n_features = len(FEATURES)

    cell_w = 0.62
    cell_h = 0.55
    label_w = 1.8
    top_pad = 2.8
    bottom_pad = 0.5

    fig_w = label_w + n_tools * cell_w + 0.4
    fig_h = top_pad + n_features * cell_h + bottom_pad - 2.5

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    x0 = label_w
    y0 = bottom_pad
    bioemma_idx = n_tools - 1

    ax.add_patch(
        plt.Rectangle(
            (x0 + bioemma_idx * cell_w, y0),
            cell_w,
            n_features * cell_h,
            facecolor=BIOEMMA_COLUMN,
            edgecolor="none",
            zorder=0,
        )
    )

    for row in range(n_features):
        for col in range(n_tools):
            color = {0: NONE, 1: FULL, 2: LIMITED}[int(MATRIX[row, col])]
            cx = x0 + col * cell_w
            cy = y0 + (n_features - 1 - row) * cell_h
            ax.add_patch(
                plt.Rectangle(
                    (cx, cy),
                    cell_w,
                    cell_h,
                    facecolor=color,
                    edgecolor=GRID,
                    linewidth=0.6,
                    zorder=1,
                )
            )

    for col, tool in enumerate(TOOLS):
        cx = x0 + col * cell_w + cell_w / 2
        cy = y0 + n_features * cell_h + 0.08
        is_bioemma = col == bioemma_idx
        ax.text(
            cx,
            cy,
            tool,
            rotation=45,
            ha="left",
            va="bottom",
            fontsize=8.5,
            fontweight="bold" if is_bioemma else "normal",
            color=BIOEMMA_HEADER if is_bioemma else "black",
            transform=ax.transData,
        )

    for row, feature in enumerate(FEATURES):
        cy = y0 + (n_features - 1 - row) * cell_h + cell_h / 2
        ax.text(x0 - 0.12, cy, feature, ha="right", va="center", fontsize=8)

    ax.legend(
        handles=[
            mpatches.Patch(facecolor=FULL, edgecolor=GRID, label="Full Support"),
            mpatches.Patch(facecolor=LIMITED, edgecolor=GRID, label="Limited Support"),
        ],
        loc="lower left",
        bbox_to_anchor=((x0 + 2) / fig_w, (y0 - 0.18) / fig_h),
        bbox_transform=fig.transFigure,
        frameon=False,
        ncol=2,
        fontsize=14,
        handlelength=1.2,
        handleheight=0.9,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(pad=0)
    plt.savefig(OUTPUT_PATH, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
