# Figure 1

Workspace for the first article figure.

Put source notebooks, scripts, intermediate data, and generated figure exports for Figure 1 here.

## Map Drafts

Build the cropped rn00010 drafts from the repository root:

```powershell
.\.venv\Scripts\python.exe figures_scripts\figure_01\build_figure_01_maps.py
```

The script keeps the Figure 1 settings at the top of the file, builds full intermediate BioEMMA maps under `outputs/_full/`, then prepares a reproducible lower-glycolysis fragment for the article draft.

Tune layout and crop settings at the top of `build_figure_01_maps.py`. The current exclude list is an article-side workaround; see `library_notes.md` for the BioEMMA issues this exposed.

Main generated files:

- `outputs/fragment/kegg_fragment.html`
- `outputs/fragment/ecoli_core_fragment.html`
- `outputs/fragment/ecoli_core_flux_fragment.html`
