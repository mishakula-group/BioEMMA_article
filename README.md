# BioEMMA Article Materials

This repository contains scripts and input files used to prepare article figures, tables, and external visualization-tool comparisons.

It intentionally does not include local virtual environments, `node_modules`, generated image files, or vendored third-party tool repositories.

## Setup

Create an environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If BioEMMA is not available as a package in your environment, install it from a local checkout instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -e C:\path\to\BioEMMA
```

## Inputs

Shared input files are in `data/`:

- `e_coli_core.xml`
- `fluxes_for_metexplore.csv`
- `model_for_fluxer.json`

Figure 3 reconstruction inputs are in `figures/figure_03/inputs/`.

## Build Materials

Figure 1:

```powershell
.\.venv\Scripts\python.exe figures\figure_01\build_figure_01_maps.py
```

Figure 2 NAViFluX-ready inputs:

```powershell
.\.venv\Scripts\python.exe figures\figure_02\build_figure_02_naviflux_inputs.py
```

Figure 3 full maps:

```powershell
.\.venv\Scripts\python.exe figures\figure_03\build_figure_03_rn00010_maps.py
.\.venv\Scripts\python.exe figures\figure_03\build_figure_03_rn00010_maps.py --pathway map00020
.\.venv\Scripts\python.exe figures\figure_03\build_figure_03_map00020_crop.py
```

Supplementary materials:

```powershell
.\.venv\Scripts\python.exe figures\supplementary_figures\build_supplementary_rn00010.py
.\.venv\Scripts\python.exe figures\supplementary_figures\build_supplementary_tool_workflows.py
```

Table 1:

```powershell
.\.venv\Scripts\python.exe figures\table_01\build_table_01.py
```

Tool comparison matrix:

```powershell
.\.venv\Scripts\python.exe scripts\build_tool_comparison_matrix.py
```

External visualization-tool inputs:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_external_tool_inputs.py --skip-optional
```

External tool launch notes are in `external_tools/`.
