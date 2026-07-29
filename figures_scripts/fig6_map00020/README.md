# Figure 6 and Supplementary S10-S13 scripts

Full map drafts for comparing `map00020` reconstruction across gapseq,
ModelSEEDpy, and Reconstructor.

Inputs are stored with normalized names:

- `inputs/gapseq.sbml` - copied from `output.xml`.
- `inputs/modelseed.sbml` - copied from the ModelSEEDpy output.
- `inputs/reconstructor.sbml` - copied from the Reconstructor output.

Build the model-specific full-layout maps from the repository root:

```powershell
.\.venv\Scripts\python.exe figures_scripts\fig6_map00020\build_model_maps.py --pathway map00020
```

Outputs are written under `outputs/<pathway>/`, one folder per tool. Use
`--include-kegg-only` only when the draft should keep every KEGG reaction instead
of filtering the layout to reactions matched in each reconstructed model.

Build the selected-reaction `map00020` crop fragments:

```powershell
.\.venv\Scripts\python.exe figures_scripts\fig6_map00020\build_map00020_fragments.py
```

Crop outputs are written under `outputs/map00020/selected_reaction_fragments/`.

Build the publication full-map flux overlays for the latest `map00020` source
models:

```powershell
.\.venv\Scripts\python.exe figures_scripts\fig6_map00020\build_map00020_full_fluxes.py
```

Curated outputs are stored in `results/figure_03/map00020/`. That results path
is kept because it is cited directly in the article.
