# Figure 4 NAViFLuX scripts

Workspace for NAViFLuX-ready comparison inputs.

The build script downloads the official Escher `e_coli_core.Core metabolism`
map, keeps only the lower-glycolysis reactions used in Figure 3, repeats the
same filtering for the BioEMMA map, and writes a reduced `e_coli_core` model
containing only those reactions.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe figures_scripts\fig4_naviflux\build_naviflux_inputs.py
```

Generated files are written to `outputs/naviflux/`:

- `official_escher_ecoli_core_map00010_reactions.html`
- `bioemma_ecoli_core_map00010_reactions.html`
- `e_coli_core_map00010_reactions.xml`
- `e_coli_core_map00010_reactions.json`
- `naviflux_reaction_weights_map00010_reactions.csv`
- `naviflux_flux_weights_map00010_reactions.csv`
- `summary.json`

The retained model reactions are `PYK`, `ENO`, `PGM`, and `PPS`. The BioEMMA
map currently labels the phosphoglycerate mutase step as `PGAM_h`, so the
script treats `PGM`, `PGAM_h`, and `R01518` as the same reaction group.

NAViFLuX launch notes and the API upload smoke check are in
`../../external_tools_launch/naviflux/README.md`.

