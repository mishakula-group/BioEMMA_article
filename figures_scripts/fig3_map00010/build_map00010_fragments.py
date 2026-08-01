from __future__ import annotations

import csv
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from bioemma.workflow import build_outputs, load_model, validate_escher_map


FIGURE_DIR = Path(__file__).resolve().parent
REPO_ROOT = FIGURE_DIR.parents[1]
DATA_DIR = REPO_ROOT / "data"

# Inputs.
PATHWAY = "rn00010"
MODEL_PATH = DATA_DIR / "e_coli_core.xml"
FLUX_CSV = DATA_DIR / "fluxes_for_metexplore.csv"
RUN_FBA_IF_FLUX_MISSING = True
USE_MODEL_METABOLITE_IDS = True

# Outputs.
OUTPUT_DIR = FIGURE_DIR / "outputs"
FULL_OUTPUT_DIR = OUTPUT_DIR / "_full"
FRAGMENT_DIR = OUTPUT_DIR / "fragment"
COBRA_CACHE_DIR = FIGURE_DIR / ".cobra_cache"

# BioEMMA layout knobs.
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

# Figure draft crop knobs.
ANCHOR_REACTIONS = {"ENO", "PYK", "R00658", "R00200"}
# Reactions that define the article fragment and must stay in the BioEMMA panel
# even if the reference KEGG crop box changes by a few pixels after layout updates.
FORCE_REACTIONS = {
    "ENO",
    "PYK",
    "PGM",
    "PGAM_h",
    "PPS",
    "R00658",
    "R00200",
    "R01518",
    "R00199",
}
EXCLUDE_REACTIONS = {
    "PPCK",
    "PEPCK_re",
    "ITPOXAL",
    "POR_syn",
    "ACLSa",
    "LDH_L",
    "R00341",
    "R00431",
    "R00726",
    "R01196",
    "R00014",
    "R00703",
}
CROP_MARGIN = 80.0
CANVAS_PADDING = 80.0
FALLBACK_MISSING_METABOLITE_LABELS = True

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


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def save_html(
    path: Path,
    map_json_path: Path,
    *,
    model: Any | None = None,
    reaction_data: dict[str, float] | None = None,
) -> None:
    import escher

    kwargs: dict[str, Any] = {"map_json": str(map_json_path)}
    if model is not None:
        kwargs["model"] = model
    if reaction_data is not None:
        kwargs["reaction_data"] = reaction_data

    path.parent.mkdir(parents=True, exist_ok=True)
    escher.Builder(**kwargs).save_html(str(path))


def reaction_ids(reaction: dict[str, Any]) -> set[str]:
    return {
        str(reaction[key])
        for key in ("name", "bigg_id")
        if reaction.get(key)
    }


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


def bbox(points: list[tuple[float, float]], margin: float = 0.0) -> dict[str, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {
        "min_x": min(xs) - margin,
        "max_x": max(xs) + margin,
        "min_y": min(ys) - margin,
        "max_y": max(ys) + margin,
    }


def crop_escher_map(
    escher_map: list[dict[str, Any]],
    *,
    map_name: str,
    map_description: str,
    reference_layout: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cropped = deepcopy(escher_map)
    model = cropped[1]
    nodes = {str(key): value for key, value in model["nodes"].items()}
    reactions = {str(key): value for key, value in model["reactions"].items()}

    anchor_reactions = {
        reaction_id: reaction
        for reaction_id, reaction in reactions.items()
        if reaction_ids(reaction) & ANCHOR_REACTIONS
    }
    anchor_points = [
        point
        for reaction in anchor_reactions.values()
        for point in reaction_points(reaction, nodes)
    ]
    crop_box = (
        reference_layout["crop_box"]
        if reference_layout is not None
        else bbox(anchor_points, margin=CROP_MARGIN)
    )

    retained_reactions = {}
    retained_node_ids: set[str] = set()
    for reaction_id, reaction in reactions.items():
        if reaction_ids(reaction) & EXCLUDE_REACTIONS:
            continue

        points = reaction_points(reaction, nodes)
        keep = bool(reaction_ids(reaction) & (ANCHOR_REACTIONS | FORCE_REACTIONS)) or any(
            crop_box["min_x"] <= x <= crop_box["max_x"]
            and crop_box["min_y"] <= y <= crop_box["max_y"]
            for x, y in points
        )
        if not keep:
            continue

        retained_reactions[reaction_id] = reaction
        for segment in reaction.get("segments", {}).values():
            retained_node_ids.add(str(segment["from_node_id"]))
            retained_node_ids.add(str(segment["to_node_id"]))

    retained_nodes = {
        node_id: node
        for node_id, node in nodes.items()
        if node_id in retained_node_ids
    }

    if FALLBACK_MISSING_METABOLITE_LABELS:
        for node in retained_nodes.values():
            if node.get("node_type") == "metabolite" and not node.get("bigg_id"):
                node["bigg_id"] = node.get("name")

    kept_points = []
    for node in retained_nodes.values():
        kept_points.extend(node_points(node))
    for reaction in retained_reactions.values():
        kept_points.extend(reaction_points(reaction, retained_nodes))
    kept_box = bbox(kept_points)

    if reference_layout is None:
        dx = CANVAS_PADDING - kept_box["min_x"]
        dy = CANVAS_PADDING - kept_box["min_y"]
        canvas = {
            "x": 0,
            "y": 0,
            "width": kept_box["max_x"] - kept_box["min_x"] + CANVAS_PADDING * 2,
            "height": kept_box["max_y"] - kept_box["min_y"] + CANVAS_PADDING * 2,
        }
    else:
        dx = reference_layout["dx"]
        dy = reference_layout["dy"]
        canvas = deepcopy(reference_layout["canvas"])
    for node in retained_nodes.values():
        for x_key, y_key in (("x", "y"), ("label_x", "label_y")):
            if x_key in node and y_key in node:
                node[x_key] = float(node[x_key]) + dx
                node[y_key] = float(node[y_key]) + dy

    for reaction in retained_reactions.values():
        for x_key, y_key in (("label_x", "label_y"),):
            if x_key in reaction and y_key in reaction:
                reaction[x_key] = float(reaction[x_key]) + dx
                reaction[y_key] = float(reaction[y_key]) + dy
        for segment in reaction.get("segments", {}).values():
            for bend_key in ("b1", "b2"):
                bend = segment.get(bend_key)
                if isinstance(bend, dict) and "x" in bend and "y" in bend:
                    bend["x"] = float(bend["x"]) + dx
                    bend["y"] = float(bend["y"]) + dy

    model["nodes"] = retained_nodes
    model["reactions"] = retained_reactions
    model["text_labels"] = {}
    model["canvas"] = canvas
    cropped[0]["map_name"] = map_name
    cropped[0]["map_description"] = map_description

    return cropped, {
        "layout": {
            "crop_box": crop_box,
            "kept_box_before_shift": kept_box,
            "dx": dx,
            "dy": dy,
            "canvas": canvas,
            "uses_reference_layout": reference_layout is not None,
        },
        "retained_reactions": [
            sorted(reaction_ids(reaction))
            for reaction in retained_reactions.values()
        ],
        "validation": validate_escher_map(cropped),
    }


def shift_escher_map(escher_map: list[dict[str, Any]], dx: float, dy: float) -> None:
    model = escher_map[1]
    for node in model["nodes"].values():
        for x_key, y_key in (("x", "y"), ("label_x", "label_y")):
            if x_key in node and y_key in node:
                node[x_key] = float(node[x_key]) + dx
                node[y_key] = float(node[y_key]) + dy

    for reaction in model["reactions"].values():
        if "label_x" in reaction and "label_y" in reaction:
            reaction["label_x"] = float(reaction["label_x"]) + dx
            reaction["label_y"] = float(reaction["label_y"]) + dy
        for segment in reaction.get("segments", {}).values():
            for bend_key in ("b1", "b2"):
                bend = segment.get(bend_key)
                if isinstance(bend, dict) and "x" in bend and "y" in bend:
                    bend["x"] = float(bend["x"]) + dx
                    bend["y"] = float(bend["y"]) + dy


def align_reaction_labels_to_reference(
    target_map: list[dict[str, Any]],
    reference_map: list[dict[str, Any]],
) -> dict[str, Any]:
    reference_labels: dict[str, tuple[float, float]] = {}
    for reaction in reference_map[1]["reactions"].values():
        if "label_x" not in reaction or "label_y" not in reaction:
            continue
        for reaction_id in reaction_ids(reaction):
            reference_labels[reaction_id] = (
                float(reaction["label_x"]),
                float(reaction["label_y"]),
            )

    offsets = []
    matched_ids = []
    for reaction in target_map[1]["reactions"].values():
        if "label_x" not in reaction or "label_y" not in reaction:
            continue
        for reaction_id in sorted(reaction_ids(reaction)):
            if reaction_id not in reference_labels:
                continue
            ref_x, ref_y = reference_labels[reaction_id]
            offsets.append(
                (
                    ref_x - float(reaction["label_x"]),
                    ref_y - float(reaction["label_y"]),
                )
            )
            matched_ids.append(reaction_id)
            break

    if not offsets:
        return {"applied": False, "reason": "no shared reaction labels"}

    dx = sum(offset[0] for offset in offsets) / len(offsets)
    dy = sum(offset[1] for offset in offsets) / len(offsets)
    shift_escher_map(target_map, dx, dy)
    return {
        "applied": True,
        "dx": dx,
        "dy": dy,
        "matched_reaction_ids": matched_ids,
    }


def visible_fluxes(escher_map: list[dict[str, Any]], fluxes: dict[str, float]) -> dict[str, float]:
    visible_reaction_ids = set()
    for reaction in escher_map[1]["reactions"].values():
        visible_reaction_ids.update(reaction_ids(reaction))
    return {
        reaction_id: value
        for reaction_id, value in fluxes.items()
        if reaction_id in visible_reaction_ids
    }


def main() -> None:
    os.environ.setdefault("BIOEMMA_COBRA_CACHE_DIR", str(COBRA_CACHE_DIR))

    fluxes = load_fluxes(FLUX_CSV)
    result = build_outputs(
        model=MODEL_PATH,
        pathway=PATHWAY,
        output_dir=FULL_OUTPUT_DIR,
        fluxes=fluxes,
        run_fba=RUN_FBA_IF_FLUX_MISSING and fluxes is None,
        save_kegg_map=True,
        save_html=False,
        use_model_metabolite_ids=USE_MODEL_METABOLITE_IDS,
        visualization_options=VISUALIZATION_OPTIONS,
    )
    fluxes = result.fluxes or {}
    for target, source in FLUX_ALIASES.items():
        if source in fluxes and target not in fluxes:
            fluxes[target] = fluxes[source]

    with result.paths["kegg_escher_map_json"].open("r", encoding="utf-8") as file:
        kegg_map = json.load(file)
    with result.paths["escher_map_json"].open("r", encoding="utf-8") as file:
        ecoli_map = json.load(file)

    kegg_fragment, kegg_meta = crop_escher_map(
        kegg_map,
        map_name="fig3_rn00010_kegg_fragment",
        map_description="Cropped KEGG rn00010 fragment for Figure 3.",
    )
    ecoli_fragment, ecoli_meta = crop_escher_map(
        ecoli_map,
        map_name="fig3_rn00010_ecoli_core_fragment",
        map_description="Cropped BioEMMA map of e_coli_core on rn00010 for Figure 3.",
        reference_layout=kegg_meta["layout"],
    )
    ecoli_alignment = align_reaction_labels_to_reference(ecoli_fragment, kegg_fragment)
    ecoli_meta["reference_alignment"] = ecoli_alignment
    ecoli_meta["validation"] = validate_escher_map(ecoli_fragment)

    flux_fragment = deepcopy(ecoli_fragment)
    flux_fragment[0]["map_name"] = "fig3_rn00010_ecoli_core_flux_fragment"
    flux_fragment[0]["map_description"] = (
        "Cropped BioEMMA map of e_coli_core on rn00010 with reaction fluxes."
    )

    output_paths = {
        "kegg_json": FRAGMENT_DIR / "kegg_fragment.json",
        "kegg_html": FRAGMENT_DIR / "kegg_fragment.html",
        "ecoli_core_json": FRAGMENT_DIR / "ecoli_core_fragment.json",
        "ecoli_core_html": FRAGMENT_DIR / "ecoli_core_fragment.html",
        "flux_json": FRAGMENT_DIR / "ecoli_core_flux_fragment.json",
        "flux_html": FRAGMENT_DIR / "ecoli_core_flux_fragment.html",
        "fragment_fluxes_json": FRAGMENT_DIR / "fluxes_fragment.json",
        "summary_json": FRAGMENT_DIR / "summary.json",
    }

    write_json(output_paths["kegg_json"], kegg_fragment)
    write_json(output_paths["ecoli_core_json"], ecoli_fragment)
    write_json(output_paths["flux_json"], flux_fragment)
    write_json(output_paths["fragment_fluxes_json"], visible_fluxes(flux_fragment, fluxes))

    cobra_model = load_model(MODEL_PATH)
    save_html(output_paths["kegg_html"], output_paths["kegg_json"])
    save_html(output_paths["ecoli_core_html"], output_paths["ecoli_core_json"])
    save_html(
        output_paths["flux_html"],
        output_paths["flux_json"],
        model=cobra_model,
        reaction_data=fluxes,
    )

    write_json(
        output_paths["summary_json"],
        {
            "pathway": PATHWAY,
            "model": str(MODEL_PATH),
            "flux_csv": str(FLUX_CSV),
            "visualization_options": VISUALIZATION_OPTIONS,
            "metabolite_id_options": {
                "use_model_metabolite_ids": USE_MODEL_METABOLITE_IDS,
            },
            "anchor_reactions": sorted(ANCHOR_REACTIONS),
            "force_reactions": sorted(FORCE_REACTIONS),
            "exclude_reactions": sorted(EXCLUDE_REACTIONS),
            "crop_margin": CROP_MARGIN,
            "canvas_padding": CANVAS_PADDING,
            "kegg_fragment": kegg_meta,
            "ecoli_core_fragment": ecoli_meta,
            "visible_fluxes": visible_fluxes(flux_fragment, fluxes),
            "outputs": {key: str(path) for key, path in output_paths.items()},
        },
    )

    for key, path in output_paths.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
