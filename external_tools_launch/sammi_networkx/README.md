# SAMMI And NetworkX

Prepare non-BioEMMA tool inputs and optional SAMMI/NetworkX outputs:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_external_tool_inputs.py
```

For input files only:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_external_tool_inputs.py --skip-optional
```

Generated files are written to `outputs/external_tools/`:

- `metexplore_fluxes.csv`
- `naviflux_reaction_weights.csv`
- `naviflux_flux_weights.csv`
- `model_for_fluxer.json`
- Fluxer GUI upload should use the SBML model `data/e_coli_core.xml`; the publication bundle also keeps a copy as `results/fig5_tool_comparison/fluxer_upload_model.xml`.
- `sammi/sammi_full.html` and `sammi/sammi_flux.html` when `sammi` is installed
- `networkx/networkx_baseline.png` when `networkx` and `matplotlib` are installed

