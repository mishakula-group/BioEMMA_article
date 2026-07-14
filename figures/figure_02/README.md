# Figure 2

Workspace for NAViFluX-ready Figure 2 inputs.

The build script downloads the official Escher `e_coli_core.Core metabolism`
map, keeps only the lower-glycolysis reactions used in Figure 1, repeats the
same filtering for the BioEMMA map, and writes a reduced `e_coli_core` model
containing only those reactions.

## Build

Run from the materials repository root:

```powershell
.\.venv\Scripts\python.exe figures\figure_02\build_figure_02_naviflux_inputs.py
```

Generated files are written to `outputs/naviflux/`:

- `official_escher_ecoli_core_figure_01_reactions.html`
- `bioemma_ecoli_core_figure_01_reactions.html`
- `e_coli_core_figure_01_reactions.xml`
- `e_coli_core_figure_01_reactions.json`
- `naviflux_reaction_weights_figure_01_reactions.csv`
- `naviflux_flux_weights_figure_01_reactions.csv`
- `summary.json`

The retained model reactions are `PYK`, `ENO`, `PGM`, and `PPS`. The BioEMMA
map currently labels the phosphoglycerate mutase step as `PGAM_h`, so the
script treats `PGM`, `PGAM_h`, and `R01518` as the same reaction group.

## NAViFluX Launch Notes

These notes are condensed from the top-level `gsmn_viz_comparison.ipynb`
notebook.

Install NAViFluX once:

```powershell
cd NAViFluX
.\install.ps1
```

If the install script is inconvenient in a notebook or conda environment, do
the manual setup:

```powershell
cd NAViFluX\server
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

cd ..\client
npm install
```

Start the backend and frontend in two terminals:

```powershell
cd NAViFluX\server
.\venv\Scripts\python.exe -m flask run
```

```powershell
cd NAViFluX\client
npm.cmd run dev
```

Open the Vite URL shown by `npm.cmd run dev`, usually
`http://localhost:5173` or `http://localhost:5174`.

On Windows, the wrapper in `external_tools/naviflux/run_naviflux_windows.ps1`
uses `npm.cmd` explicitly to avoid PowerShell execution-policy failures.

In the NAViFluX interface:

1. Upload Options -> Model File -> `figures/figure_02/outputs/naviflux/e_coli_core_figure_01_reactions.xml`
2. Upload Options -> Reaction Weight File -> `figures/figure_02/outputs/naviflux/naviflux_reaction_weights_figure_01_reactions.csv`
3. Upload Options -> Flux Weight File -> `figures/figure_02/outputs/naviflux/naviflux_flux_weights_figure_01_reactions.csv`
4. Open Pathway Visualizer and choose a layout such as Hierarchical-LR, Circo, Stress, or Neato.

For API-based checking, the notebook used these local endpoints:

```python
NAVIFLUX_API = "http://127.0.0.1:5000"

with open("figures/figure_02/outputs/naviflux/e_coli_core_figure_01_reactions.xml", "rb") as f:
    response = session.post(
        f"{NAVIFLUX_API}/api/v1/cobra-model",
        files={"file": ("e_coli_core_figure_01_reactions.xml", f, "application/xml")},
        timeout=60,
    )
```
