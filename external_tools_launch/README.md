# External Visualization Tools

The article comparison used several tools that are not BioEMMA itself. This repository keeps reproducible inputs, wrappers, and notes, but does not vendor third-party source trees or local environments.

- `naviflux/` - launch wrapper and API upload smoke check.
- `grohar/` - legacy setup notes.
- `sammi_networkx/` - SAMMI and NetworkX input/output generation notes.

Fluxer, CAVE, and MetExplore V2 were run through their web interfaces for the
article comparison. Their retained publication outputs are in
`results/fig5_tool_comparison/`, and the exact workflow notes are in
`figures_scripts/supplementary_figures/supplementary_tool_workflows.md`.

Run the shared preparation script from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_external_tool_inputs.py --skip-optional
```
