from __future__ import annotations

import html
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "results" / "fig5_tool_comparison"
OUTPUT_PATH = OUTPUT_DIR / "tool_comparison_matrix.png"
HTML_OUTPUT_PATH = OUTPUT_DIR / "tool_comparison.html"

TOOLS = [
    "CytoSEED",
    "CAVE",
    "Grohar",
    "Fluxer",
    "MetExplore V2",
    "ModelExplorer",
    "SAMMI",
    "Escher",
    "NAViFluX",
    "BioEMMA",
]

FEATURES = [
    "Standard model format input\n(SBML / JSON)",
    "Pathway / subsystem-level\nvisualization",
    "Flux data overlay",
    "Web-browser\nmap interface",
    "Static map export\n(SVG / PNG / PDF)",
    "Offline / local execution",
    "Programmatic access",
    "Automatic map generation",
    "Native Escher-compatible\nJSON output",
]

# 0 = no support, 1 = full support, 2 = limited support.
# Columns follow TOOLS order.
MATRIX = np.array(
    [
        # Standard model format input (SBML / JSON)
        [1, 1, 1, 1, 1, 2, 1, 1, 1, 1],
        # Pathway / subsystem-level visualization
        [1, 1, 1, 2, 1, 0, 1, 1, 1, 1],
        # Flux data overlay
        [2, 1, 1, 1, 1, 2, 1, 1, 1, 1],
        # Web-browser map interface
        [0, 1, 0, 1, 1, 0, 1, 1, 1, 2],
        # Static map export (SVG / PNG / PDF)
        [2, 1, 2, 1, 1, 0, 1, 1, 1, 2],
        # Offline / local execution
        [2, 0, 1, 0, 0, 1, 2, 1, 1, 1],
        # Programmatic access
        [0, 0, 0, 0, 1, 0, 2, 2, 2, 1],
        # Automatic map generation
        [2, 1, 1, 1, 1, 1, 1, 0, 1, 1],
        # Native Escher-compatible JSON output
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
    ],
    dtype=int,
)

FULL = "#68B740"
LIMITED = "#F3DE3D"
NONE = "#FFFFFF"
GRID = "#CCCCCC"
BIOEMMA_COLUMN = "#E8F4F8"
BIOEMMA_HEADER = "#68B740"


def support_label(value: int) -> str:
    return {0: "No support", 1: "Full support", 2: "Limited support"}[int(value)]


def support_class(value: int) -> str:
    return {0: "none", 1: "full", 2: "limited"}[int(value)]


def write_html_table(path: Path) -> None:
    rows = []
    rows.append("<table>")
    rows.append("  <thead>")
    rows.append("    <tr>")
    rows.append("      <th>Feature</th>")
    for tool in TOOLS:
        classes = "tool bioemma" if tool == "BioEMMA" else "tool"
        rows.append(f"      <th class=\"{classes}\">{html.escape(tool)}</th>")
    rows.append("    </tr>")
    rows.append("  </thead>")
    rows.append("  <tbody>")

    for feature, values in zip(FEATURES, MATRIX, strict=True):
        rows.append("    <tr>")
        rows.append(
            "      <th class=\"feature\">"
            + html.escape(feature).replace("\n", "<br>")
            + "</th>"
        )
        for value in values:
            label = support_label(int(value))
            rows.append(
                f"      <td class=\"{support_class(int(value))}\">{html.escape(label)}</td>"
            )
        rows.append("    </tr>")

    rows.append("  </tbody>")
    rows.append("</table>")

    document = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Tool comparison matrix</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 24px;
      color: #222;
      background: #fff;
    }
    table {
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      border: 1px solid #cccccc;
      padding: 8px 10px;
      text-align: center;
      vertical-align: middle;
    }
    th.feature {
      text-align: right;
      white-space: nowrap;
      font-weight: 600;
    }
    th.tool {
      font-weight: 600;
    }
    th.bioemma {
      color: #3f8f2c;
      background: #e8f4f8;
    }
    td.full {
      background: #68b740;
    }
    td.limited {
      background: #f3de3d;
    }
    td.none {
      background: #ffffff;
    }
  </style>
</head>
<body>
"""
    document += "\n".join(rows)
    document += """
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")


def main() -> None:
    n_tools = len(TOOLS)
    n_features = len(FEATURES)

    if MATRIX.shape != (n_features, n_tools):
        raise ValueError(
            f"Matrix shape {MATRIX.shape} does not match "
            f"{n_features} features x {n_tools} tools"
        )

    cell_w = 0.62
    cell_h = 0.55
    label_w = 1.8
    top_pad = 2.8
    bottom_pad = 0.9

    fig_w = label_w + n_tools * cell_w + 0.4
    fig_h = top_pad + n_features * cell_h + bottom_pad - 2.1

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
        loc="upper center",
        bbox_to_anchor=(x0 + n_tools * cell_w / 2, y0 - 0.22),
        bbox_transform=ax.transData,
        frameon=False,
        ncol=2,
        fontsize=10.5,
        handlelength=1.2,
        handleheight=0.9,
        columnspacing=1.8,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(pad=0)
    plt.savefig(OUTPUT_PATH, dpi=220, bbox_inches="tight", facecolor="white")
    write_html_table(HTML_OUTPUT_PATH)
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {HTML_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
