from __future__ import annotations

import csv
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


FIGURE_DIR = Path(__file__).resolve().parent
REPO_ROOT = FIGURE_DIR.parents[1]
DATA_DIR = REPO_ROOT / "data"

# Inputs.
PATHWAY = "rn00010"
MODEL_PATH = DATA_DIR / "e_coli_core.xml"
FLUX_CSV = DATA_DIR / "fluxes_for_metexplore.csv"
FIGURE_01_FULL_MAP = (
    REPO_ROOT / "figures" / "figure_01" / "outputs" / "_full" / PATHWAY / "escher_map.json"
)
OFFICIAL_ESCHER_MAP_NAME = "e_coli_core.Core metabolism"
USE_MODEL_METABOLITE_IDS = True

# Outputs.
OUTPUT_DIR = FIGURE_DIR / "outputs" / "naviflux"
COBRA_CACHE_DIR = FIGURE_DIR / ".cobra_cache"

# Figure 1 lower-glycolysis reactions retained on the e_coli_core/BioEMMA panel.
# PGM is the model reaction ID; PGAM_h is the current BioEMMA map alias.
REACTION_GROUPS = {
    "PYK": {"PYK", "R00200"},
    "ENO": {"ENO", "R00658"},
    "PGM": {"PGM", "PGAM_h", "R01518"},
    "PPS": {"PPS", "R00199"},
}
MODEL_REACTIONS_TO_KEEP = tuple(REACTION_GROUPS.keys())
ALL_REACTION_ALIASES = set().union(*REACTION_GROUPS.values())
FLUX_ALIASES = {"PGM": "PGAM_h", "PGAM_h": "PGM"}
CANVAS_PADDING = 80.0

# Same BioEMMA layout knobs as Figure 1, to keep the comparison stable.
VISUALIZATION_OPTIONS = {
    "scaling_factor": 4.0,
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


def configure_cobra_cache() -> None:
    """Keep cobrapy cache inside the figure workspace before cobra imports."""
    os.environ.setdefault("BIOEMMA_COBRA_CACHE_DIR", str(COBRA_CACHE_DIR))

    import appdirs

    original_user_cache_dir = appdirs.user_cache_dir

    def user_cache_dir(appname=None, appauthor=None, *args, **kwargs):
        if appname == "cobrapy" and appauthor == "opencobra":
            return str(COBRA_CACHE_DIR)
        return original_user_cache_dir(appname, appauthor, *args, **kwargs)

    appdirs.user_cache_dir = user_cache_dir


configure_cobra_cache()

from bioemma.workflow import build_outputs, load_model, validate_escher_map  # noqa: E402


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def reaction_ids(reaction: dict[str, Any]) -> set[str]:
    return {
        str(reaction[key])
        for key in ("name", "bigg_id")
        if reaction.get(key)
    }


def canonical_reaction_ids(reaction: dict[str, Any]) -> list[str]:
    ids = reaction_ids(reaction)
    return [
        canonical
        for canonical, aliases in REACTION_GROUPS.items()
        if ids & aliases
    ]


def node_points(node: dict[str, Any]) -> list[tuple[float, float]]:
    points = []
    for x_key, y_key in (("x", "y"), ("label_x", "label_y")):
        if x_key in node and y_key in node:
            points.append((float(node[x_key]), float(node[y_key])))
    return points


def reaction_points(
    reaction: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
) -> list[tuple[float, float]]:
    points = []
    if "label_x" in reaction and "label_y" in reaction:
        points.append((float(reaction["label_x"]), float(reaction["label_y"])))

    for segment in reaction.get("segments", {}).values():
        for bend_key in ("b1", "b2"):
            bend = segment.get(bend_key)
            if isinstance(bend, dict) and "x" in bend and "y" in bend:
                points.append((float(bend["x"]), float(bend["y"])))
        for node_key in ("from_node_id", "to_node_id"):
            node = nodes.get(str(segment.get(node_key)))
            if node:
                points.extend(node_points(node))
    return points


def bbox(points: list[tuple[float, float]]) -> dict[str, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
    }


def retune_canvas(escher_map: list[dict[str, Any]]) -> dict[str, Any]:
    model = escher_map[1]
    nodes = model["nodes"]
    reactions = model["reactions"]
    points = []
    for node in nodes.values():
        points.extend(node_points(node))
    for reaction in reactions.values():
        points.extend(reaction_points(reaction, nodes))

    kept_box = bbox(points)
    dx = CANVAS_PADDING - kept_box["min_x"]
    dy = CANVAS_PADDING - kept_box["min_y"]
    canvas = {
        "x": 0,
        "y": 0,
        "width": kept_box["max_x"] - kept_box["min_x"] + CANVAS_PADDING * 2,
        "height": kept_box["max_y"] - kept_box["min_y"] + CANVAS_PADDING * 2,
    }

    for node in nodes.values():
        for x_key, y_key in (("x", "y"), ("label_x", "label_y")):
            if x_key in node and y_key in node:
                node[x_key] = float(node[x_key]) + dx
                node[y_key] = float(node[y_key]) + dy

    for reaction in reactions.values():
        if "label_x" in reaction and "label_y" in reaction:
            reaction["label_x"] = float(reaction["label_x"]) + dx
            reaction["label_y"] = float(reaction["label_y"]) + dy
        for segment in reaction.get("segments", {}).values():
            for bend_key in ("b1", "b2"):
                bend = segment.get(bend_key)
                if isinstance(bend, dict) and "x" in bend and "y" in bend:
                    bend["x"] = float(bend["x"]) + dx
                    bend["y"] = float(bend["y"]) + dy

    model["canvas"] = canvas
    return {"kept_box_before_shift": kept_box, "dx": dx, "dy": dy, "canvas": canvas}


def filter_escher_map(
    escher_map: list[dict[str, Any]],
    *,
    map_name: str,
    map_description: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    filtered = deepcopy(escher_map)
    model = filtered[1]
    nodes = {str(key): value for key, value in model["nodes"].items()}
    reactions = {str(key): value for key, value in model["reactions"].items()}

    retained_reactions = {}
    retained_node_ids: set[str] = set()
    retained_canonical_ids = []

    for reaction_id, reaction in reactions.items():
        canonical = canonical_reaction_ids(reaction)
        if not canonical:
            continue
        retained_reactions[reaction_id] = reaction
        retained_canonical_ids.extend(canonical)
        for segment in reaction.get("segments", {}).values():
            retained_node_ids.add(str(segment["from_node_id"]))
            retained_node_ids.add(str(segment["to_node_id"]))

    retained_nodes = {
        node_id: node
        for node_id, node in nodes.items()
        if node_id in retained_node_ids
    }

    model["nodes"] = retained_nodes
    model["reactions"] = retained_reactions
    model["text_labels"] = {}
    filtered[0]["map_name"] = map_name
    filtered[0]["map_description"] = map_description
    layout = retune_canvas(filtered)

    missing = sorted(set(MODEL_REACTIONS_TO_KEEP) - set(retained_canonical_ids))
    return filtered, {
        "retained_reactions": [
            {
                "map_reaction_id": reaction_id,
                "ids": sorted(reaction_ids(reaction)),
                "canonical_ids": canonical_reaction_ids(reaction),
            }
            for reaction_id, reaction in retained_reactions.items()
        ],
        "missing_canonical_reactions": missing,
        "layout": layout,
        "validation": validate_escher_map(filtered),
    }


def load_fluxes(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}

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


def write_naviflux_weight_files(fluxes: dict[str, float]) -> dict[str, Path]:
    rows = [
        {"id": reaction_id, "value": fluxes.get(reaction_id, 0.0)}
        for reaction_id in MODEL_REACTIONS_TO_KEEP
    ]
    paths = {
        "reaction_weights": OUTPUT_DIR / "naviflux_reaction_weights_figure_01_reactions.csv",
        "flux_weights": OUTPUT_DIR / "naviflux_flux_weights_figure_01_reactions.csv",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=("id", "value"))
            writer.writeheader()
            writer.writerows(rows)
    return paths


def save_html(path: Path, map_json_path: Path, *, model: Any | None = None) -> None:
    import escher

    kwargs: dict[str, Any] = {"map_json": str(map_json_path)}
    if model is not None:
        kwargs["model"] = model

    path.parent.mkdir(parents=True, exist_ok=True)
    escher.Builder(**kwargs).save_html(str(path))


def load_or_build_bioemma_map() -> list[dict[str, Any]]:
    if FIGURE_01_FULL_MAP.exists():
        with FIGURE_01_FULL_MAP.open("r", encoding="utf-8") as file:
            return json.load(file)

    result = build_outputs(
        model=MODEL_PATH,
        pathway=PATHWAY,
        output_dir=OUTPUT_DIR / "_bioemma_full",
        fluxes=load_fluxes(FLUX_CSV),
        run_fba=False,
        save_kegg_map=False,
        save_html=False,
        use_model_metabolite_ids=USE_MODEL_METABOLITE_IDS,
        visualization_options=VISUALIZATION_OPTIONS,
    )
    return result.escher_map


def write_reduced_model() -> tuple[Path, Path, dict[str, Any]]:
    import cobra

    model = load_model(MODEL_PATH)
    original_counts = {
        "reactions": len(model.reactions),
        "metabolites": len(model.metabolites),
        "genes": len(model.genes),
    }

    keep = set(MODEL_REACTIONS_TO_KEEP)
    missing = sorted(keep - {reaction.id for reaction in model.reactions})
    remove = [reaction for reaction in model.reactions if reaction.id not in keep]
    model.remove_reactions(remove, remove_orphans=True)
    if "PYK" in model.reactions:
        model.objective = "PYK"
    elif model.reactions:
        model.objective = model.reactions[0]

    sbml_path = OUTPUT_DIR / "e_coli_core_figure_01_reactions.xml"
    json_path = OUTPUT_DIR / "e_coli_core_figure_01_reactions.json"
    sbml_path.parent.mkdir(parents=True, exist_ok=True)
    cobra.io.write_sbml_model(model, str(sbml_path))
    cobra.io.save_json_model(model, str(json_path))

    return sbml_path, json_path, {
        "source_model": str(MODEL_PATH),
        "objective": str(model.objective.expression),
        "kept_reactions": [reaction.id for reaction in model.reactions],
        "missing_requested_reactions": missing,
        "original_counts": original_counts,
        "reduced_counts": {
            "reactions": len(model.reactions),
            "metabolites": len(model.metabolites),
            "genes": len(model.genes),
        },
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    from escher.plots import map_json_for_name

    official_source = json.loads(map_json_for_name(OFFICIAL_ESCHER_MAP_NAME))
    bioemma_source = load_or_build_bioemma_map()

    official_source_path = OUTPUT_DIR / "official_escher_ecoli_core_source.json"
    write_json(official_source_path, official_source)

    official_filtered, official_meta = filter_escher_map(
        official_source,
        map_name="figure_02_official_escher_ecoli_core_figure_01_reactions",
        map_description=(
            "Official Escher e_coli_core map filtered to the Figure 1 "
            "lower-glycolysis reactions."
        ),
    )
    official_json = OUTPUT_DIR / "official_escher_ecoli_core_figure_01_reactions.json"
    official_html = OUTPUT_DIR / "official_escher_ecoli_core_figure_01_reactions.html"
    bioemma_json = OUTPUT_DIR / "bioemma_ecoli_core_figure_01_reactions.json"
    bioemma_html = OUTPUT_DIR / "bioemma_ecoli_core_figure_01_reactions.html"

    write_json(official_json, official_filtered)
    bioemma_filtered, bioemma_meta = filter_escher_map(
        bioemma_source,
        map_name="figure_02_bioemma_ecoli_core_figure_01_reactions",
        map_description=(
            "BioEMMA e_coli_core rn00010 map filtered to the Figure 1 "
            "lower-glycolysis reactions."
        ),
    )
    write_json(bioemma_json, bioemma_filtered)

    reduced_sbml, reduced_json, reduced_model_meta = write_reduced_model()
    cobra_model = load_model(MODEL_PATH)
    save_html(official_html, official_json, model=cobra_model)
    save_html(bioemma_html, bioemma_json, model=cobra_model)

    fluxes = load_fluxes(FLUX_CSV)
    weight_paths = write_naviflux_weight_files(fluxes)
    visible_fluxes = {
        reaction_id: fluxes.get(reaction_id, 0.0)
        for reaction_id in MODEL_REACTIONS_TO_KEEP
    }

    output_paths = {
        "official_source_json": official_source_path,
        "official_filtered_json": official_json,
        "official_filtered_html": official_html,
        "bioemma_filtered_json": bioemma_json,
        "bioemma_filtered_html": bioemma_html,
        "reduced_sbml": reduced_sbml,
        "reduced_json": reduced_json,
        **weight_paths,
        "summary_json": OUTPUT_DIR / "summary.json",
    }
    write_json(
        output_paths["summary_json"],
        {
            "pathway": PATHWAY,
            "official_escher_map_name": OFFICIAL_ESCHER_MAP_NAME,
            "reaction_groups": {
                key: sorted(value)
                for key, value in REACTION_GROUPS.items()
            },
            "model_reactions_to_keep": list(MODEL_REACTIONS_TO_KEEP),
            "metabolite_id_options": {
                "use_model_metabolite_ids": USE_MODEL_METABOLITE_IDS,
            },
            "official_escher_filtered_map": official_meta,
            "bioemma_filtered_map": bioemma_meta,
            "reduced_model": reduced_model_meta,
            "visible_fluxes": visible_fluxes,
            "outputs": {key: str(path) for key, path in output_paths.items()},
        },
    )

    for key, path in output_paths.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
