from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cobra
from bioemma._resources import resource_path
from bioemma.metanetx_mapper import MetaNetXMapper

from build_figure_03_map00020_crop import (
    build_flux_overlay_map,
    save_flux_html,
    write_json,
)


FIGURE_DIR = Path(__file__).resolve().parent
REPO_ROOT = FIGURE_DIR.parents[1]
RESULTS_DIR = REPO_ROOT / "results" / "figure_03" / "map00020"
SOURCE_MODEL_DIR = RESULTS_DIR / "source_models"

MODELS = {
    "gapseq": SOURCE_MODEL_DIR / "SRR13921546_ecoli_M9_vit_aa_gapseq.xml",
    "modelseed": SOURCE_MODEL_DIR / "SRR13921546_ecoli_M9_vit_aa_ModelSEED.sbml",
    "reconstructor": SOURCE_MODEL_DIR / "SRR13921546_ecoli_M9_vit_aa_Reconstructor.sbml",
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_full_flux_overlay(
    slug: str,
    model_path: Path,
    reaction_mapper: MetaNetXMapper,
) -> dict[str, str]:
    source_map_path = RESULTS_DIR / slug / f"{slug}_map00020_map.json"
    flux_map_json_path = RESULTS_DIR / slug / f"{slug}_map00020_full_flux_map.json"
    flux_json_path = RESULTS_DIR / slug / f"{slug}_map00020_full_fluxes.json"
    flux_html_path = RESULTS_DIR / slug / f"{slug}_map00020_full_with_fluxes.html"

    escher_map = read_json(source_map_path)
    model = cobra.io.read_sbml_model(str(model_path))
    solution = model.optimize()
    flux_map, reaction_data, matches = build_flux_overlay_map(
        escher_map,
        model=model,
        solution=solution,
        reaction_mapper=reaction_mapper,
    )

    write_json(flux_map_json_path, flux_map)
    write_json(
        flux_json_path,
        {
            "model": str(model_path.relative_to(REPO_ROOT)),
            "source_map": str(source_map_path.relative_to(REPO_ROOT)),
            "solution_status": str(solution.status),
            "objective_value": (
                None
                if solution.objective_value is None
                else float(solution.objective_value)
            ),
            "reaction_data": reaction_data,
            "matches": matches,
        },
    )
    save_flux_html(flux_html_path, flux_map_json_path, reaction_data)

    return {
        "flux_map_json": str(flux_map_json_path),
        "flux_json": str(flux_json_path),
        "flux_html": str(flux_html_path),
    }


def main() -> None:
    missing = [str(path) for path in MODELS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Figure 3 source models: " + ", ".join(missing))

    reaction_mapper = MetaNetXMapper(resource_path("reaction_mapping.tsv"), "first")
    outputs = {
        slug: build_full_flux_overlay(slug, model_path, reaction_mapper)
        for slug, model_path in MODELS.items()
    }

    for slug, paths in outputs.items():
        print(f"{slug}: {paths['flux_html']}")


if __name__ == "__main__":
    main()
