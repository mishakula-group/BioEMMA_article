# Figure 3 and Supplementary S1-S4 scripts

Workspace for the lower-glycolysis `map00010` / `rn00010` BioEMMA map panels.

Build the cropped drafts from the repository root:

```powershell
.\.venv\Scripts\python.exe figures_scripts\fig3_map00010\build_map00010_fragments.py
```

The script builds full intermediate BioEMMA maps under `outputs/_full/`, then
prepares reproducible lower-glycolysis fragments under `outputs/fragment/`.
Curated copies for readers are stored in `results/fig3_map00010/` and
`results/supplementary/rn00010/`.

Tune layout and crop settings at the top of `build_map00010_fragments.py`. The
current exclude list is an article-side workaround; see `library_notes.md` for
the BioEMMA issues this exposed.

Main generated files:

- `outputs/fragment/kegg_fragment.html`
- `outputs/fragment/ecoli_core_fragment.html`
- `outputs/fragment/ecoli_core_flux_fragment.html`

