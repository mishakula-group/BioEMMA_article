from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from bioemma._resources import resource_path
from bioemma.metanetx_mapper import MetaNetXMapper
from bioemma.workflow import validate_escher_map


FIGURE_DIR = Path(__file__).resolve().parent
PATHWAY = "map00020"
FULL_OUTPUT_DIR = FIGURE_DIR / "outputs" / PATHWAY
CROP_OUTPUT_DIR = FULL_OUTPUT_DIR / "selected_reaction_fragments"
COBRA_CACHE_DIR = FIGURE_DIR / ".cobra_cache"
INPUT_DIR = FIGURE_DIR / "inputs"
CANVAS_PADDING = 80.0
REACTION_COMPARTMENT_SUFFIX = re.compile(r"^(.+)_([a-z]\d*|[a-z])$")

MODELS = (
    ("gapseq", "gapseq"),
    ("modelseed", "ModelSEED"),
    ("reconstructor", "Reconstructor"),
)

FRAGMENTS = {
    "cs_pdh_por_aconitase": {
        "label": "CS / PDH / POR / aconitase fragment",
        "requested_reactions": (
            "CS",
            "PDHam1h",
            "POR_syn",
            "ACLS3",
            "ACONTa",
            "ACONTb",
        ),
    },
    "aconitase_icd_osucc": {
        "label": "Aconitase / ICD / OSUCC fragment",
        "requested_reactions": (
            "ACONTb",
            "ICDHx",
            "r0422",
            "r0082",
            "ICITRED",
            "OSUCCL",
        ),
    },
}

REACTION_ALIASES = {
    "CS": {"CS", "R00351"},
    "ACONTa": {"ACONTa", "ACONTa_1", "ACN_a_m", "R01325"},
    "ACONTb": {"ACONTb", "ACONTb_1", "ACN_b_m", "R01900"},
    "PC": {"PC", "R00344"},
    "PDHam1h": {"PDHam1h", "PDHam1hi", "PDHam1m", "ACLSa", "R00014"},
    "ACLS3": {"ACLS3", "ACLSa", "PDHam1h", "PDHam1hi", "PDHam1m", "R00014"},
    "POR_syn": {"POR_syn", "PYRShi", "R01196"},
    "ICDHx": {"ICDHx", "ICDHxm", "R00709"},
    "r0422": {"r0422", "r0423", "r0424", "ICITRED", "R01899"},
    "r0082": {"r0082", "r0083", "r0084", "OSUCCL", "R00268"},
    "ICITRED": {"ICITRED", "r0422", "r0423", "r0424", "R01899"},
    "OSUCCL": {"OSUCCL", "r0082", "r0083", "r0084", "R00268"},
    "r0763": {"r0763", "rxn00763", "R01036"},
    "SUCCtm": {"SUCCtm", "SUCCt2m", "R_SUCCtm", "R_SUCCt2m"},
    "SUCCt": {"SUCCt", "R_SUCCt"},
    "ASCT": {"ASCT", "ASCTmr", "SUCOAACTr", "R10343"},
    "ASCTtm": {"ASCTtm", "ASCTmr", "SUCOAACTr", "R10343"},
    "R_SUCCtm": {"R_SUCCtm", "SUCCtm", "SUCCt2m", "R_SUCCt2m"},
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def save_html(path: Path, map_json_path: Path) -> None:
    import escher

    path.parent.mkdir(parents=True, exist_ok=True)
    escher.Builder(map_json=str(map_json_path)).save_html(str(path))


def save_flux_html(
    path: Path,
    map_json_path: Path,
    reaction_data: dict[str, float],
) -> None:
    import escher

    path.parent.mkdir(parents=True, exist_ok=True)
    escher.Builder(
        map_json=str(map_json_path),
        reaction_data=reaction_data,
    ).save_html(str(path))


def configure_cobra_cache() -> None:
    os.environ.setdefault("BIOEMMA_COBRA_CACHE_DIR", str(COBRA_CACHE_DIR))
    COBRA_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    import appdirs

    original_user_cache_dir = appdirs.user_cache_dir

    def user_cache_dir(appname=None, appauthor=None, *args, **kwargs):
        if appname == "cobrapy" and appauthor == "opencobra":
            return str(COBRA_CACHE_DIR)
        return original_user_cache_dir(appname, appauthor, *args, **kwargs)

    appdirs.user_cache_dir = user_cache_dir


def model_path(model_slug: str) -> Path:
    return INPUT_DIR / f"{model_slug}.sbml"


def load_cobra_model(model_slug: str):
    import cobra

    return cobra.io.read_sbml_model(str(model_path(model_slug)))


def load_models() -> dict[str, Any]:
    return {slug: load_cobra_model(slug) for slug, _label in MODELS}


def optimize_models(models: dict[str, Any]) -> dict[str, Any]:
    return {slug: model.optimize() for slug, model in models.items()}


def annotation_values(annotation: dict[str, Any], key: str) -> list[str]:
    values = annotation.get(key, [])
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    elif not isinstance(values, (list, tuple, set)):
        values = [values]
    return [str(value) for value in values if value]


def strip_reaction_compartment(reaction_id: str) -> str:
    match = REACTION_COMPARTMENT_SUFFIX.match(reaction_id)
    return match.group(1) if match else reaction_id


def model_reaction_ids(reaction: Any) -> set[str]:
    ids = {str(reaction.id), strip_reaction_compartment(str(reaction.id))}
    ids.update(annotation_values(reaction.annotation, "kegg.reaction"))
    ids.update(annotation_values(reaction.annotation, "bigg.reaction"))
    ids.update(annotation_values(reaction.annotation, "seed.reaction"))
    return {value for value in ids if value}


def expand_reaction_aliases(
    ids: set[str],
    mapper: MetaNetXMapper,
) -> set[str]:
    aliases = set(ids)
    for reaction_id in list(ids):
        if reaction_id in mapper:
            entry = mapper[reaction_id]
            aliases.add(entry.kegg)
            aliases.update(entry.bigg_all)
            aliases.update(entry.seed_all)
            continue

        for database in ("bigg", "seed"):
            for entry in mapper.reverse_lookup(database, reaction_id):
                aliases.add(entry.kegg)
                aliases.update(entry.bigg_all)
                aliases.update(entry.seed_all)

    return {value for value in aliases if value}


def build_model_reaction_index(
    model: Any,
    mapper: MetaNetXMapper,
) -> dict[str, Any]:
    index = {}
    for reaction in model.reactions:
        for reaction_id in expand_reaction_aliases(model_reaction_ids(reaction), mapper):
            index.setdefault(reaction_id, reaction)
    return index


def reaction_ids(reaction: dict[str, Any]) -> set[str]:
    values = {
        str(reaction[key])
        for key in ("name", "bigg_id")
        if reaction.get(key)
    }
    return {value for value in values if value and value != "None"}


def map_reaction_aliases(
    reaction: dict[str, Any],
    mapper: MetaNetXMapper,
) -> set[str]:
    return expand_reaction_aliases(reaction_ids(reaction), mapper)


def requested_matches(
    reaction: dict[str, Any],
    requested_reactions: tuple[str, ...],
) -> set[str]:
    ids = reaction_ids(reaction)
    return {
        requested
        for requested in requested_reactions
        for aliases in [REACTION_ALIASES[requested]]
        if ids & aliases
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


def collect_crop_points(
    escher_map: list[dict[str, Any]],
    requested_reactions: tuple[str, ...],
) -> list[tuple[float, float]]:
    model = escher_map[1]
    nodes = {str(key): value for key, value in model["nodes"].items()}
    points = []
    for reaction in model["reactions"].values():
        if requested_matches(reaction, requested_reactions):
            points.extend(reaction_points(reaction, nodes))
    return points


def shift_map(escher_map: list[dict[str, Any]], dx: float, dy: float) -> None:
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


def crop_map(
    escher_map: list[dict[str, Any]],
    *,
    model_slug: str,
    model_label: str,
    fragment_slug: str,
    fragment_label: str,
    requested_reactions: tuple[str, ...],
    canvas: dict[str, float],
    dx: float,
    dy: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cropped = deepcopy(escher_map)
    model = cropped[1]
    nodes = {str(key): value for key, value in model["nodes"].items()}
    reactions = {str(key): value for key, value in model["reactions"].items()}

    retained_reactions = {}
    retained_node_ids: set[str] = set()
    requested_to_reactions = {requested: [] for requested in requested_reactions}

    for reaction_id, reaction in reactions.items():
        matches = requested_matches(reaction, requested_reactions)
        if not matches:
            continue

        retained_reactions[reaction_id] = reaction
        for requested in matches:
            requested_to_reactions[requested].append(
                {
                    "reaction_json_id": reaction_id,
                    "name": reaction.get("name"),
                    "bigg_id": reaction.get("bigg_id"),
                }
            )
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
    model["canvas"] = deepcopy(canvas)
    cropped[0]["map_name"] = f"figure_03_{PATHWAY}_{model_slug}_{fragment_slug}"
    cropped[0]["map_id"] = f"{PATHWAY}_{model_slug}_{fragment_slug}"
    cropped[0]["map_description"] = (
        f"{model_label} reconstruction mapped to KEGG rn00020; "
        f"cropped to {fragment_label}."
    )

    shift_map(cropped, dx, dy)
    validation = validate_escher_map(cropped)

    return cropped, {
        "requested_to_reactions": requested_to_reactions,
        "found_requested_reactions": [
            requested
            for requested, matches in requested_to_reactions.items()
            if matches
        ],
        "missing_requested_reactions": [
            requested
            for requested, matches in requested_to_reactions.items()
            if not matches
        ],
        "retained_reactions": [
            {
                "reaction_json_id": reaction_id,
                "ids": sorted(reaction_ids(reaction)),
            }
            for reaction_id, reaction in retained_reactions.items()
        ],
        "validation": validation,
    }


def build_flux_overlay_map(
    escher_map: list[dict[str, Any]],
    *,
    model: Any,
    solution: Any,
    reaction_mapper: MetaNetXMapper,
) -> tuple[list[dict[str, Any]], dict[str, float], list[dict[str, Any]]]:
    flux_map = deepcopy(escher_map)
    if getattr(solution, "fluxes", None) is None:
        return flux_map, {}, []

    model_index = build_model_reaction_index(model, reaction_mapper)
    reaction_data = {}
    matches = []

    for reaction in flux_map[1]["reactions"].values():
        original_map_ids = sorted(reaction_ids(reaction))
        map_reaction_id = reaction.get("bigg_id") or reaction.get("name")
        aliases = map_reaction_aliases(reaction, reaction_mapper)
        model_reaction = next(
            (model_index[alias] for alias in sorted(aliases) if alias in model_index),
            None,
        )
        if model_reaction is None:
            matches.append(
                {
                    "map_reaction_ids": original_map_ids,
                    "model_reaction_id": None,
                    "flux": None,
                }
            )
            continue

        flux = float(solution.fluxes[model_reaction.id])
        reaction_data[str(map_reaction_id)] = flux
        matches.append(
            {
                "map_reaction_ids": original_map_ids,
                "map_reaction_id": str(map_reaction_id),
                "model_reaction_id": model_reaction.id,
                "flux": flux,
            }
        )

    return flux_map, reaction_data, matches


def main() -> None:
    configure_cobra_cache()

    source_maps = {
        slug: read_json(FULL_OUTPUT_DIR / slug / f"{slug}_{PATHWAY}_map.json")
        for slug, _label in MODELS
    }
    cobra_models = load_models()
    model_solutions = optimize_models(cobra_models)
    reaction_mapper = MetaNetXMapper(resource_path("reaction_mapping.tsv"), "first")
    fragment_summaries = {}
    fragment_outputs = {}

    for fragment_slug, fragment in FRAGMENTS.items():
        requested_reactions = fragment["requested_reactions"]
        fragment_label = fragment["label"]
        all_points = [
            point
            for escher_map in source_maps.values()
            for point in collect_crop_points(escher_map, requested_reactions)
        ]
        if not all_points:
            raise ValueError(f"No selected reactions were found for {fragment_slug}.")

        crop_box = bbox(all_points, margin=CANVAS_PADDING)
        dx = CANVAS_PADDING - crop_box["min_x"]
        dy = CANVAS_PADDING - crop_box["min_y"]
        canvas = {
            "x": 0,
            "y": 0,
            "width": crop_box["max_x"] - crop_box["min_x"] + CANVAS_PADDING * 2,
            "height": crop_box["max_y"] - crop_box["min_y"] + CANVAS_PADDING * 2,
        }

        summaries = {}
        outputs = {}
        for slug, label in MODELS:
            cropped, meta = crop_map(
                source_maps[slug],
                model_slug=slug,
                model_label=label,
                fragment_slug=fragment_slug,
                fragment_label=fragment_label,
                requested_reactions=requested_reactions,
                canvas=canvas,
                dx=dx,
                dy=dy,
            )
            json_path = (
                CROP_OUTPUT_DIR
                / fragment_slug
                / f"{slug}_{PATHWAY}_{fragment_slug}.json"
            )
            html_path = (
                CROP_OUTPUT_DIR
                / fragment_slug
                / f"{slug}_{PATHWAY}_{fragment_slug}.html"
            )
            flux_json_path = (
                CROP_OUTPUT_DIR
                / fragment_slug
                / f"{slug}_{PATHWAY}_{fragment_slug}_fluxes.json"
            )
            flux_map_json_path = (
                CROP_OUTPUT_DIR
                / fragment_slug
                / f"{slug}_{PATHWAY}_{fragment_slug}_flux_map.json"
            )
            flux_html_path = (
                CROP_OUTPUT_DIR
                / fragment_slug
                / f"{slug}_{PATHWAY}_{fragment_slug}_with_fluxes.html"
            )
            flux_map, reaction_data, flux_matches = build_flux_overlay_map(
                cropped,
                model=cobra_models[slug],
                solution=model_solutions[slug],
                reaction_mapper=reaction_mapper,
            )
            write_json(json_path, cropped)
            save_html(html_path, json_path)
            write_json(flux_map_json_path, flux_map)
            write_json(
                flux_json_path,
                {
                    "model": str(model_path(slug)),
                    "solution_status": str(model_solutions[slug].status),
                    "objective_value": (
                        None
                        if model_solutions[slug].objective_value is None
                        else float(model_solutions[slug].objective_value)
                    ),
                    "reaction_data": reaction_data,
                    "matches": flux_matches,
                },
            )
            save_flux_html(
                flux_html_path,
                flux_map_json_path,
                reaction_data,
            )
            meta["fluxes"] = {
                "solution_status": str(model_solutions[slug].status),
                "objective_value": (
                    None
                    if model_solutions[slug].objective_value is None
                    else float(model_solutions[slug].objective_value)
                ),
                "reaction_count": len(reaction_data),
                "matches": flux_matches,
            }
            summaries[slug] = meta
            outputs[slug] = {
                "json": str(json_path),
                "html": str(html_path),
                "flux_map_json": str(flux_map_json_path),
                "flux_json": str(flux_json_path),
                "flux_html": str(flux_html_path),
            }

        fragment_summaries[fragment_slug] = {
            "label": fragment_label,
            "requested_reactions": list(requested_reactions),
            "reaction_aliases": {
                key: sorted(values)
                for key, values in REACTION_ALIASES.items()
                if key in requested_reactions
            },
            "layout": {
                "crop_box": crop_box,
                "dx": dx,
                "dy": dy,
                "canvas": canvas,
            },
            "models": summaries,
        }
        fragment_outputs[fragment_slug] = outputs

    summary_path = CROP_OUTPUT_DIR / "summary.json"
    write_json(
        summary_path,
        {
            "pathway": PATHWAY,
            "source_dir": str(FULL_OUTPUT_DIR),
            "fragments": fragment_summaries,
            "outputs": fragment_outputs,
        },
    )

    for fragment_slug, outputs in fragment_outputs.items():
        for slug, paths in outputs.items():
            print(f"{fragment_slug}/{slug}: {paths['flux_html']}")
    print(f"summary: {summary_path}")


if __name__ == "__main__":
    main()
