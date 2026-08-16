# Supplementary Figures

Full-map drafts for supplementary materials.

Build the full rn00010 maps from the repository root:

```powershell
.\.venv\Scripts\python.exe figures_scripts\supplementary_figures\build_supplementary_rn00010.py
```

Outputs are written under `outputs/rn00010/`.

## Tool Workflow Supplement

Build the supplementary comparison figure for the non-NAViFluX tools:

```powershell
.\.venv\Scripts\python.exe figures_scripts\supplementary_figures\build_supplementary_tool_workflows.py
```

Outputs are written under `outputs/tool_workflows/`:

- `supplementary_tool_workflows.svg`
- `supplementary_tool_workflows.html`

The accompanying code notes are in `supplementary_tool_workflows.md`.

