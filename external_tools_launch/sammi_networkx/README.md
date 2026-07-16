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
- `sammi/sammi_full.html` and `sammi/sammi_flux.html` when `sammi` is installed
- `networkx/networkx_baseline.png` when `networkx` and `matplotlib` are installed
