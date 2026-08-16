# Supplementary Tool Workflows

This note collects the non-NAViFluX tool workflows used for the article
comparison. NAViFLuX is documented with Figure 4 and in `external_tools_launch/naviflux/`;
the tools below remain in supplementary materials.

## SAMMI

SAMMI is the most direct Python route for an interactive de novo HTML graph.

```python
import os
import numpy as np
import sammi

opts = sammi.options()
opts.htmlName = os.path.join(os.getcwd(), "sammi_full.html")
opts.load = False
sammi.plot(model, opts=opts)

opts_flux = sammi.options()
opts_flux.htmlName = "sammi_flux.html"
opts_flux.load = False

flux_data = sammi.data(
    group="reactions",
    kind="color",
    data=np.array(solution.fluxes.values).reshape(-1, 1),
    ids=list(solution.fluxes.index),
    conditions=np.array(["FBA fluxes"]),
)

sammi.plot(model, datat=[flux_data], opts=opts_flux)
```

Outputs:

- `sammi_full.html`
- `sammi_flux.html`

## MetExplore V2

The notebook first tries the REST route. If the public API is unavailable, use
the web interface manually and keep the same flux CSV for overlay.

```python
import requests

METEXPLORE_BASE = "https://metexplore.toulouse.inrae.fr/metexplore2/"

with open(SBML_PATH, "rb") as f:
    response = requests.post(
        METEXPLORE_BASE + "api/1/network/sbml",
        files={"file": f},
        timeout=60,
    )
```

Flux overlay file:

```python
me_fluxes = solution.fluxes.reset_index()
me_fluxes.columns = ["reactionId", "flux"]
me_fluxes[me_fluxes["flux"].abs() > 1e-6].to_csv(
    "fluxes_for_metexplore.csv",
    index=False,
)
```

Manual fallback:

1. Open `https://metexplore.toulouse.inrae.fr`.
2. Use Guest login or a personal account.
3. New Network -> Upload SBML -> select `e_coli_core.xml`.
4. Use Analysis -> Mapping to upload `fluxes_for_metexplore.csv`.

## Fluxer And CAVE

Fluxer and CAVE were treated as web-upload tools. The shared preparation step
is saving a COBRA JSON model.

```python
import cobra

cobra.io.save_json_model(model, "model_for_fluxer.json")
```

Outputs and uploads:

- Fluxer: upload `model_for_fluxer.json`, then run FBA.
- CAVE: upload the SBML model directly or use the JSON model where accepted.

## Grohar

Grohar needs an isolated legacy environment because it depends on old COBRApy
APIs.

```python
import os
import subprocess
import sys

GROHAR_DIR = "./Grohar"
GROHAR_VENV = os.path.join(GROHAR_DIR, "venv")

if not os.path.isdir(GROHAR_VENV):
    subprocess.run([sys.executable, "-m", "venv", GROHAR_VENV], check=True)

venv_pip = os.path.join(GROHAR_VENV, "Scripts", "pip.exe")
for pkg in [
    "cobra==0.5.4",
    "PyQt5",
    "bioservices",
    "msgpack",
    "python-libsbml",
    "plotly",
    "pydot",
    "networkx",
    "scipy",
]:
    subprocess.run([venv_pip, "install", pkg], check=True)
```

The notebook also used a non-GUI structural fallback around `pyr_c` with
NetworkX after importing Grohar's `model_data` and `make_pairs` modules. The
saved output is `grohar_output.png`.

## NetworkX Baseline

The baseline graph is a pure-Python fallback: load the model through COBRApy,
run FBA, build a directed bipartite reaction-metabolite graph, color reaction
nodes by absolute flux, and save a static PNG.

```python
import networkx as nx

G = nx.DiGraph()
for reaction in model.reactions:
    flux = solution.fluxes.get(reaction.id, 0.0)
    if abs(flux) < 1e-9:
        continue
    G.add_node(reaction.id, node_type="reaction", flux=flux)
    for metabolite, coefficient in reaction.metabolites.items():
        if coefficient < 0:
            G.add_edge(metabolite.id, reaction.id, weight=abs(coefficient))
        else:
            G.add_edge(reaction.id, metabolite.id, weight=abs(coefficient))
```

Output:

- `networkx_baseline.png`

