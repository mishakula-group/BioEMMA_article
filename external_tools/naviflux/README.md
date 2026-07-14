# NAViFluX

This repository does not vendor NAViFluX. Install or clone NAViFluX separately, then build the Figure 2 inputs:

```powershell
.\.venv\Scripts\python.exe figures\figure_02\build_figure_02_naviflux_inputs.py
```

Start NAViFluX on Windows:

```powershell
.\external_tools\naviflux\run_naviflux_windows.ps1 -NavifluxDir C:\path\to\NAViFluX
```

The wrapper uses `npm.cmd` instead of `npm` to avoid PowerShell execution-policy failures, and sets a local cache root for the Flask process.

After launch, upload:

- `figures/figure_02/outputs/naviflux/e_coli_core_figure_01_reactions.xml`
- `figures/figure_02/outputs/naviflux/naviflux_reaction_weights_figure_01_reactions.csv`
- `figures/figure_02/outputs/naviflux/naviflux_flux_weights_figure_01_reactions.csv`

Optional API smoke check:

```powershell
.\.venv\Scripts\python.exe external_tools\naviflux\check_naviflux_upload.py
```
