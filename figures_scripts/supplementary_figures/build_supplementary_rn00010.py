from __future__ import annotations

import csv
import os
from pathlib import Path

from bioemma.workflow import build_outputs


FIGURE_DIR = Path(__file__).resolve().parent
REPO_ROOT = FIGURE_DIR.parents[1]
DATA_DIR = REPO_ROOT / "data"

# Inputs.
PATHWAY = "rn00010"
MODEL_PATH = DATA_DIR / "e_coli_core.xml"
FLUX_CSV = DATA_DIR / "fluxes_for_metexplore.csv"
RUN_FBA_IF_FLUX_MISSING = True

# Outputs.
OUTPUT_DIR = FIGURE_DIR / "outputs"
COBRA_CACHE_DIR = FIGURE_DIR / ".cobra_cache"

# Same BioEMMA layout knobs as Figure 1.
VISUALIZATION_OPTIONS = {
    "scaling_factor": 5.0,
    "axis_epsilon": 2.0,
    "markers_dist": 10.0,
    "metabolite_label_shift": (-13.0, -5.0),
    "reaction_label_shift": (5.0, 5.0),
    "canvas_margin_x": 160.0,
    "canvas_margin_y": 160.0,
    "multimarker_distance_fraction": 0.2,
    "use_constant_multimarker_distance": False,
    "constant_multimarker_distance": 300.0,
    "axis_offset": 20.0,
    "secondary_metabolite_distance": 15.0,
    "secondary_metabolite_spacing": 20.0,
}

# The flux table uses the e_coli_core ID, while the BioEMMA map currently exposes PGAM_h.
FLUX_ALIASES = {"PGAM_h": "PGM"}


def load_fluxes(path: Path) -> dict[str, float] | None:
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fluxes = {
            row["reactionId"].strip(): float(row["flux"])
            for row in reader
            if row.get("reactionId") and row.get("flux")
        }

    for target, source in FLUX_ALIASES.items():
        if source in fluxes and target not in fluxes:
            fluxes[target] = fluxes[source]

    return fluxes


def main() -> None:
    os.environ.setdefault("BIOEMMA_COBRA_CACHE_DIR", str(COBRA_CACHE_DIR))

    fluxes = load_fluxes(FLUX_CSV)
    result = build_outputs(
        model=MODEL_PATH,
        pathway=PATHWAY,
        output_dir=OUTPUT_DIR,
        fluxes=fluxes,
        run_fba=RUN_FBA_IF_FLUX_MISSING and fluxes is None,
        save_kegg_map=True,
        save_html=True,
        visualization_options=VISUALIZATION_OPTIONS,
    )

    for key, path in result.paths.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
