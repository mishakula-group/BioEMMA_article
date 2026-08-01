from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bioemma._resources import resource_path
from bioemma.metanetx_mapper import MetaNetXMapper
from bioemma.workflow import build_outputs, validate_escher_map


FIGURE_DIR = Path(__file__).resolve().parent
DEFAULT_PATHWAY = "rn00010"
DATABASE = "BIGG"
SEED_ID_PATTERN = re.compile(r"^(cpd\d+)(?:_([A-Za-z]\d*|[a-z]))?$")
MANUAL_SEED_TO_BIGG = {
    "cpd00001": "h2o",
    "cpd00009": "pi",
    "cpd00102": "g3p",
    "cpd00260": "icit",
}

INPUT_DIR = FIGURE_DIR / "inputs"
COBRA_CACHE_DIR = FIGURE_DIR / ".cobra_cache"

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


@dataclass(frozen=True)
class ModelSpec:
    slug: str
    label: str
    filename: str

    @property
    def path(self) -> Path:
        return INPUT_DIR / self.filename


MODELS = (
    ModelSpec("gapseq", "gapseq", "gapseq.sbml"),
    ModelSpec("modelseed", "ModelSEED", "modelseed.sbml"),
    ModelSpec("reconstructor", "Reconstructor", "reconstructor.sbml"),
)


def load_metabolite_mapper() -> MetaNetXMapper:
    return MetaNetXMapper(resource_path("metabolite_mapping.tsv"), "first")


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def save_html(path: Path, map_json_path: Path) -> None:
    import escher

    builder = escher.Builder(map_json=str(map_json_path))
    builder.save_html(str(path))


def normalize_requested_pathway(pathway: str) -> tuple[str, str]:
    value = pathway.strip()
    if value.startswith("map"):
        return f"rn{value[3:]}", value
    if value.startswith("rn"):
        return value, value
    if value.isdigit():
        return f"rn{value}", f"rn{value}"
    return value, value


def rename_map(
    escher_map: list[dict[str, Any]],
    model: ModelSpec,
    *,
    output_slug: str,
    workflow_pathway: str,
    include_kegg_only: bool,
) -> None:
    mode = "full_kegg" if include_kegg_only else "model_reconstruction"
    escher_map[0]["map_name"] = f"fig6_{output_slug}_{model.slug}_{mode}"
    escher_map[0]["map_id"] = f"{output_slug}_{model.slug}_{mode}"
    escher_map[0]["map_description"] = (
        f"{model.label} reconstruction mapped to KEGG {workflow_pathway}; "
        "full pathway layout, no figure crop."
    )


def seed_to_bigg_id(seed_like_id: str, mapper: MetaNetXMapper) -> str | None:
    match = SEED_ID_PATTERN.match(seed_like_id)
    if not match:
        return None

    seed_id = match.group(1)
    if seed_id in MANUAL_SEED_TO_BIGG:
        return MANUAL_SEED_TO_BIGG[seed_id]

    for entry in mapper.reverse_lookup("seed", seed_id):
        if entry.bigg:
            return entry.bigg
    return None


def normalize_secondary_metabolite_ids(
    escher_map: list[dict[str, Any]],
    mapper: MetaNetXMapper,
) -> dict[str, int]:
    stats = {
        "secondary_nodes_seen": 0,
        "secondary_nodes_converted": 0,
        "reaction_metabolites_seen": 0,
        "reaction_metabolites_converted": 0,
    }
    model = escher_map[1]

    for node in model["nodes"].values():
        if (
            node.get("node_type") != "metabolite"
            or node.get("node_is_primary") is not False
        ):
            continue

        stats["secondary_nodes_seen"] += 1
        mapped_id = seed_to_bigg_id(str(node.get("bigg_id", "")), mapper)
        if mapped_id:
            node["bigg_id"] = mapped_id
            stats["secondary_nodes_converted"] += 1

    for reaction in model["reactions"].values():
        for metabolite in reaction.get("metabolites", []):
            stats["reaction_metabolites_seen"] += 1
            mapped_id = seed_to_bigg_id(str(metabolite.get("bigg_id", "")), mapper)
            if mapped_id:
                metabolite["bigg_id"] = mapped_id
                stats["reaction_metabolites_converted"] += 1

    return stats


def remove_invalid_segments(escher_map: list[dict[str, Any]]) -> dict[str, int]:
    model = escher_map[1]
    node_ids = {str(node_id) for node_id in model["nodes"]}
    stats = {"segments_seen": 0, "segments_removed": 0}

    for reaction in model["reactions"].values():
        valid_segments = {}
        for segment_id, segment in reaction.get("segments", {}).items():
            stats["segments_seen"] += 1
            if (
                str(segment.get("from_node_id")) not in node_ids
                or str(segment.get("to_node_id")) not in node_ids
            ):
                stats["segments_removed"] += 1
                continue
            valid_segments[segment_id] = segment
        reaction["segments"] = valid_segments

    return stats


def build_model_map(
    model: ModelSpec,
    *,
    workflow_pathway: str,
    output_slug: str,
    output_root: Path,
    metabolite_mapper: MetaNetXMapper,
    include_kegg_only: bool,
) -> dict[str, Any]:
    output_dir = output_root / model.slug
    output_dir.mkdir(parents=True, exist_ok=True)

    map_json_path = output_dir / f"{model.slug}_{output_slug}_map.json"
    html_path = output_dir / f"{model.slug}_{output_slug}_map.html"

    result = build_outputs(
        model=model.path,
        pathway=workflow_pathway,
        map_json_path=map_json_path,
        database=DATABASE,
        visualization_options=VISUALIZATION_OPTIONS,
        include_kegg_only=include_kegg_only,
        use_database_secondary_metabolite_ids=True,
        save_kegg_map=False,
        save_html=False,
    )

    rename_map(
        result.escher_map,
        model,
        output_slug=output_slug,
        workflow_pathway=workflow_pathway,
        include_kegg_only=include_kegg_only,
    )
    normalization_stats = normalize_secondary_metabolite_ids(
        result.escher_map,
        metabolite_mapper,
    )
    segment_cleanup_stats = remove_invalid_segments(result.escher_map)
    write_json(map_json_path, result.escher_map)
    save_html(html_path, map_json_path)

    summary = dict(result.summary)
    summary["escher"] = validate_escher_map(result.escher_map)
    summary["map_build"] = {
        "tool": model.label,
        "input_model": str(model.path),
        "requested_pathway": output_slug,
        "workflow_pathway": workflow_pathway,
        "database": DATABASE,
        "include_kegg_only": include_kegg_only,
        "secondary_metabolite_bigg_normalization": normalization_stats,
        "invalid_segment_cleanup": segment_cleanup_stats,
        "map_json": str(map_json_path),
        "map_html": str(html_path),
    }
    write_json(output_dir / "summary.json", summary)

    return {
        "tool": model.label,
        "slug": model.slug,
        "input_model": str(model.path),
        "map_json": str(map_json_path),
        "map_html": str(html_path),
        "summary_json": str(output_dir / "summary.json"),
        "model": summary["model"],
        "map_stats": summary.get("map_stats", {}).get("model_matching", {}),
        "secondary_metabolite_bigg_normalization": normalization_stats,
        "invalid_segment_cleanup": segment_cleanup_stats,
        "escher": summary["escher"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build full KEGG maps for reconstruction-tool models."
    )
    parser.add_argument(
        "--pathway",
        default=DEFAULT_PATHWAY,
        help="KEGG pathway/map ID to build, e.g. rn00010 or map00020.",
    )
    parser.add_argument(
        "--include-kegg-only",
        action="store_true",
        help="Keep KEGG-only pathway reactions instead of filtering to each model.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ.setdefault("BIOEMMA_COBRA_CACHE_DIR", str(COBRA_CACHE_DIR))
    workflow_pathway, output_slug = normalize_requested_pathway(args.pathway)
    output_root = FIGURE_DIR / "outputs" / output_slug

    missing = [str(model.path) for model in MODELS if not model.path.exists()]
    if missing:
        raise FileNotFoundError("Missing source model inputs: " + ", ".join(missing))

    metabolite_mapper = load_metabolite_mapper()
    summaries = [
        build_model_map(
            model,
            workflow_pathway=workflow_pathway,
            output_slug=output_slug,
            output_root=output_root,
            metabolite_mapper=metabolite_mapper,
            include_kegg_only=args.include_kegg_only,
        )
        for model in MODELS
    ]

    overview = {
        "requested_pathway": args.pathway,
        "output_slug": output_slug,
        "workflow_pathway": workflow_pathway,
        "database": DATABASE,
        "include_kegg_only": args.include_kegg_only,
        "models": summaries,
    }
    write_json(output_root / "map_build_summary.json", overview)

    for item in summaries:
        print(f"{item['tool']}: {item['map_html']}")
    print(f"summary: {output_root / 'map_build_summary.json'}")


if __name__ == "__main__":
    main()
