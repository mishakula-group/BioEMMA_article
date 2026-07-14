from __future__ import annotations

import html
import textwrap
from pathlib import Path


FIGURE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = FIGURE_DIR / "outputs" / "tool_workflows"


TOOLS = [
    {
        "name": "SAMMI",
        "input": "SBML via COBRApy",
        "automation": "Python package",
        "output": "Interactive HTML",
        "artifact": "sammi_full.html / sammi_flux.html",
    },
    {
        "name": "MetExplore V2",
        "input": "SBML + flux CSV",
        "automation": "REST when available, web UI fallback",
        "output": "Web network view",
        "artifact": "fluxes_for_metexplore.csv",
    },
    {
        "name": "Fluxer / CAVE",
        "input": "COBRA JSON or SBML",
        "automation": "Web upload",
        "output": "FBA-oriented web view",
        "artifact": "model_for_fluxer.json",
    },
    {
        "name": "Grohar",
        "input": "SBML",
        "automation": "Separate legacy venv / GUI",
        "output": "Local subnet visualization",
        "artifact": "grohar_output.png",
    },
    {
        "name": "NetworkX baseline",
        "input": "COBRA model + FBA fluxes",
        "automation": "Pure Python",
        "output": "Static graph",
        "artifact": "networkx_baseline.png",
    },
]


def wrapped_text(
    text: str,
    *,
    x: int,
    y: int,
    width_chars: int,
    line_height: int = 16,
    size: int = 13,
    weight: str = "400",
    fill: str = "#1f2933",
) -> str:
    lines = textwrap.wrap(text, width=width_chars) or [""]
    tspan = []
    for i, line in enumerate(lines):
        dy = 0 if i == 0 else line_height
        tspan.append(
            f'<tspan x="{x}" dy="{dy}">{html.escape(line)}</tspan>'
        )
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}">'
        + "".join(tspan)
        + "</text>"
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    width = 1320
    height = 760
    margin_x = 40
    top = 150
    header_h = 54
    row_h = 106
    col_widths = [190, 245, 345, 245, 255]
    columns = ["Tool", "Input", "Automation", "Output", "Saved artifact"]

    xs = [margin_x]
    for col_w in col_widths[:-1]:
        xs.append(xs[-1] + col_w)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        wrapped_text(
            "Supplementary figure: workflows for non-NAViFluX visualization tools",
            x=margin_x,
            y=58,
            width_chars=95,
            size=24,
            weight="700",
            fill="#172033",
        ),
        wrapped_text(
            "Each row records the minimal reproducible route used in the comparison notebook.",
            x=margin_x,
            y=94,
            width_chars=110,
            size=15,
            fill="#4b5563",
        ),
    ]

    header_fill = "#203864"
    edge = "#c8d0dc"
    for label, x, col_w in zip(columns, xs, col_widths):
        parts.append(
            f'<rect x="{x}" y="{top}" width="{col_w}" height="{header_h}" '
            f'fill="{header_fill}" stroke="{header_fill}"/>'
        )
        parts.append(
            wrapped_text(
                label,
                x=x + 14,
                y=top + 34,
                width_chars=max(10, col_w // 12),
                size=14,
                weight="700",
                fill="#ffffff",
            )
        )

    for row_idx, tool in enumerate(TOOLS):
        y = top + header_h + row_idx * row_h
        fill = "#f6f8fb" if row_idx % 2 == 0 else "#ffffff"
        values = [
            tool["name"],
            tool["input"],
            tool["automation"],
            tool["output"],
            tool["artifact"],
        ]
        for value, x, col_w in zip(values, xs, col_widths):
            parts.append(
                f'<rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" '
                f'fill="{fill}" stroke="{edge}" stroke-width="1"/>'
            )
            parts.append(
                wrapped_text(
                    value,
                    x=x + 14,
                    y=y + 36,
                    width_chars=max(12, col_w // 11),
                    size=14,
                    weight="700" if x == xs[0] else "400",
                )
            )

    parts.append(
        wrapped_text(
            "Detailed commands and code snippets are in supplementary_tool_workflows.md.",
            x=margin_x,
            y=height - 42,
            width_chars=110,
            size=14,
            fill="#4b5563",
        )
    )
    parts.append("</svg>")

    output_svg = OUTPUT_DIR / "supplementary_tool_workflows.svg"
    output_html = OUTPUT_DIR / "supplementary_tool_workflows.html"
    svg = "\n".join(parts)
    output_svg.write_text(svg, encoding="utf-8")
    output_html.write_text(
        "<!doctype html><meta charset='utf-8'><title>Supplementary tool workflows</title>"
        f"<body style='margin:0'>{svg}</body>",
        encoding="utf-8",
    )
    print(f"svg: {output_svg}")
    print(f"html: {output_html}")


if __name__ == "__main__":
    main()
