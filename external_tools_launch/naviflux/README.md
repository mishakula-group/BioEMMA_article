# NAViFluX

This repository does not vendor NAViFLuX. Install or clone NAViFLuX separately,
then build the Figure 4 inputs:

```powershell
.\.venv\Scripts\python.exe figures_scripts\fig4_naviflux\build_naviflux_inputs.py
```

Start NAViFluX on Windows:

```powershell
.\external_tools_launch\naviflux\run_naviflux_windows.ps1 -NavifluxDir C:\path\to\NAViFluX
```

The wrapper uses `npm.cmd` instead of `npm` to avoid PowerShell execution-policy failures, and sets a local cache root for the Flask process.

After launch, upload:

- `figures_scripts/fig4_naviflux/outputs/naviflux/e_coli_core_map00010_reactions.xml`
- `figures_scripts/fig4_naviflux/outputs/naviflux/naviflux_reaction_weights_map00010_reactions.csv`
- `figures_scripts/fig4_naviflux/outputs/naviflux/naviflux_flux_weights_map00010_reactions.csv`

Optional API smoke check:

```powershell
.\.venv\Scripts\python.exe external_tools_launch\naviflux\check_naviflux_upload.py
```
