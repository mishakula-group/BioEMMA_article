# BioEMMA Article Materials

This repository contains the publication materials used for the BioEMMA article:
prepared figures, supplementary files, comparison artifacts, source data, and the
scripts needed to regenerate the tables and maps.

For readers, start with `results/`. The script folders are included for
reproducibility and provenance.

## Repository layout

- `results/` - publication-ready materials grouped by figure, table, and supplement.
- `data/` - shared source inputs, including the KEGG pathway list used for the all-pathway mapping table.
- `figures_scripts/` - scripts used to build figure-specific BioEMMA, Escher, and NAViFLuX materials.
- `tables_scripts/` - scripts used to build article tables.
- `external_tools_launch/` - launch notes for external visualization tools.
- `scripts/` - small helper scripts for external-tool input preparation and comparison-matrix generation.

Generated working folders named `outputs/` are intentionally ignored by git. Curated outputs
that should be visible to readers are copied into `results/`.

## Results

- `results/figure_01/fragment/` - cropped KEGG and BioEMMA Figure 1 map panels, including the flux-overlay panel.
- `results/figure_02/naviflux_full_reference/` - Figure 2 NAViFLuX reference PNG images.
- `results/figure_03/map00020/` - Figure 3 `map00020` full maps, selected reaction fragments, source models, and full-map flux overlays.
- `results/table_01/` - Table 1 reaction-retention statistics for `map00010`, `map00020`, and `map00030`.
- `results/table_02_kegg_database_mapping/` - KEGG-to-SEED/BiGG mapping counts for every pathway listed in `data/kegg_pathways.tsv`.
- `results/supplementary/` - supplementary full `rn00010` map materials.
- `results/external_tool_comparison/` - selected external-tool comparison artifacts.

## Reproducing materials

Create an environment from this repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If BioEMMA is not installed as a package, install it from a local checkout:

```powershell
.\.venv\Scripts\python.exe -m pip install -e C:\path\to\BioEMMA
```

Common rebuild commands:

```powershell
.\.venv\Scripts\python.exe figures_scripts\figure_01\build_figure_01_maps.py
.\.venv\Scripts\python.exe figures_scripts\figure_02\build_figure_02_naviflux_inputs.py
.\.venv\Scripts\python.exe figures_scripts\figure_03\build_figure_03_rn00010_maps.py --pathway map00020
.\.venv\Scripts\python.exe figures_scripts\figure_03\build_figure_03_map00020_crop.py
.\.venv\Scripts\python.exe figures_scripts\figure_03\build_figure_03_map00020_full_fluxes.py
.\.venv\Scripts\python.exe tables_scripts\table_01\build_table_01.py
.\.venv\Scripts\python.exe tables_scripts\table_02_kegg_database_mapping\build_table_02.py
```

The all-pathway KEGG mapping table is built from `data/kegg_pathways.tsv`; it does not
download KGML files from KEGG.
