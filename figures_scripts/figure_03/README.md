# Figure 3

Full `rn00010` map drafts for comparing pathway reconstruction across three tools.

Inputs are stored with normalized names:

- `inputs/gapseq.sbml.xml` - copied from `output.xml`
- `inputs/modelseed.sbml.xml` - copied from `MS_reconstructed_model.sbml.xml`
- `inputs/reconstructor.sbml.xml` - copied from `model.sbml.xml`

Build the model-specific full-layout maps from the repository root:

```powershell
.\.venv\Scripts\python.exe figures_scripts\figure_03\build_figure_03_rn00010_maps.py
```

Use another KEGG map/pathway ID when needed:

```powershell
.\.venv\Scripts\python.exe figures_scripts\figure_03\build_figure_03_rn00010_maps.py --pathway map00020
```

Outputs are written under `outputs/<pathway>/`, one folder per tool. Use
`--include-kegg-only` only when the draft should keep every KEGG reaction instead
of filtering the layout to reactions matched in each reconstructed model.
The Escher map identifiers are emitted with BIGG priority for visualization,
while matching can still use KEGG, BIGG, or SEED annotations present in the input
models. Secondary metabolites are also emitted with selected-database priority
instead of raw model IDs.

Build the selected-reaction `map00020` crop fragments:

```powershell
.\.venv\Scripts\python.exe figures_scripts\figure_03\build_figure_03_map00020_crop.py
```

Crop outputs are written under `outputs/map00020/selected_reaction_fragments/`.

Build publication full-map flux overlays for the latest `map00020` source models:

```powershell
.\.venv\Scripts\python.exe figures_scripts\figure_03\build_figure_03_map00020_full_fluxes.py
```

These overlays are written to `results/figure_03/map00020/<model>/`.
