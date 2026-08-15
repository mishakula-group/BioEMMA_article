from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[1]
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT
    / "outputs"
    / "bigg_prokaryote_bioemma"
)
DEFAULT_OUTPUT_DIRNAMES = {
    "ecoli": "ecoli_reaction_reproducibility",
    "all-prokaryotes": "all_models_reaction_reproducibility",
}
OUTPUT_PREFIXES = {
    "ecoli": "ecoli",
    "all-prokaryotes": "all_models",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def percent(value: float) -> float:
    return round(value * 100.0, 2)


def round_float(value: float | int | str | None, digits: int = 4) -> str:
    if value in ("", None):
        return ""
    return str(round(float(value), digits))


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def pipe(values) -> str:
    return "|".join(str(value) for value in sorted(values))


def select_models(
    inventory_rows: list[dict[str, str]],
    *,
    scope: str,
    excluded_models: set[str],
) -> dict[str, dict[str, str]]:
    selected = {}
    for row in inventory_rows:
        model_id = row.get("bigg_id", "")
        organism = row.get("organism", "")
        if model_id in excluded_models:
            continue
        if scope == "ecoli" and "Escherichia coli" not in organism:
            continue
        if scope not in {"ecoli", "all-prokaryotes"}:
            raise ValueError(f"Unsupported scope: {scope}")
        selected[model_id] = row
    return dict(sorted(selected.items()))


def pathway_metadata(map_stats_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    pathways = {}
    for row in map_stats_rows:
        pathway = row.get("pathway", "")
        if not pathway or pathway in pathways:
            continue
        pathways[pathway] = {
            "pathway": pathway,
            "pathway_rn": row.get("pathway_rn", ""),
            "pathway_label": row.get("pathway_label", ""),
        }
    return dict(sorted(pathways.items()))


def load_map_reactions(map_json_path: Path) -> list[dict[str, str]]:
    data = json.loads(map_json_path.read_text(encoding="utf-8"))
    body = data[1] if isinstance(data, list) and len(data) > 1 else {}
    rows = []
    for node_id, reaction in body.get("reactions", {}).items():
        kegg_reaction_id = str(reaction.get("name") or "").strip()
        model_reaction_id = str(reaction.get("bigg_id") or "").strip()
        metabolites = reaction.get("metabolites", [])
        rows.append(
            {
                "reaction_node_id": node_id,
                "kegg_reaction_id": kegg_reaction_id,
                "model_reaction_id": model_reaction_id,
                "metabolite_count": len(metabolites),
                "metabolite_bigg_ids": pipe(
                    met.get("bigg_id", "")
                    for met in metabolites
                    if met.get("bigg_id")
                ),
            }
        )
    return sorted(rows, key=lambda row: (row["kegg_reaction_id"], row["model_reaction_id"]))


def build_reaction_tables(
    output_root: Path,
    models: dict[str, dict[str, str]],
    pathways: dict[str, dict[str, str]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, dict[str, set[str]]],
    dict[str, dict[str, set[str]]],
]:
    long_rows = []
    count_rows = []
    reaction_sets: dict[str, dict[str, set[str]]] = defaultdict(dict)
    observed_bigg: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for pathway, pathway_meta in pathways.items():
        for model_id, model_meta in models.items():
            map_json_path = (
                output_root
                / "maps"
                / pathway
                / model_id
                / f"{model_id}_{pathway}_map.json"
            )
            if not map_json_path.exists():
                reaction_sets[pathway][model_id] = set()
                count_rows.append(
                    {
                        **pathway_meta,
                        "model_id": model_id,
                        "organism": model_meta.get("organism", ""),
                        "reaction_count": 0,
                        "reaction_set": "",
                        "map_json": str(map_json_path),
                        "status": "missing_map_json",
                    }
                )
                continue

            reactions = load_map_reactions(map_json_path)
            kegg_set = {
                row["kegg_reaction_id"]
                for row in reactions
                if row["kegg_reaction_id"]
            }
            reaction_sets[pathway][model_id] = kegg_set

            for row in reactions:
                kegg_reaction_id = row["kegg_reaction_id"]
                model_reaction_id = row["model_reaction_id"]
                if kegg_reaction_id and model_reaction_id:
                    observed_bigg[pathway][kegg_reaction_id].add(model_reaction_id)
                long_rows.append(
                    {
                        **pathway_meta,
                        "model_id": model_id,
                        "organism": model_meta.get("organism", ""),
                        **row,
                        "map_json": str(map_json_path),
                    }
                )

            count_rows.append(
                {
                    **pathway_meta,
                    "model_id": model_id,
                    "organism": model_meta.get("organism", ""),
                    "reaction_count": len(kegg_set),
                    "reaction_set": pipe(kegg_set),
                    "map_json": str(map_json_path),
                    "status": "ok",
                }
            )

    return long_rows, count_rows, reaction_sets, observed_bigg


def build_pairwise_tables(
    reaction_sets: dict[str, dict[str, set[str]]],
    models: dict[str, dict[str, str]],
    pathways: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pairwise_rows = []
    diff_rows = []
    summary_rows = []

    for pathway, model_sets in sorted(reaction_sets.items()):
        pathway_meta = pathways[pathway]
        model_ids = sorted(model_sets)
        jaccards = []
        identical_pairs = 0
        for model_a, model_b in combinations(model_ids, 2):
            set_a = model_sets[model_a]
            set_b = model_sets[model_b]
            intersection = set_a & set_b
            union = set_a | set_b
            only_a = set_a - set_b
            only_b = set_b - set_a
            jaccard = len(intersection) / len(union) if union else 1.0
            jaccards.append(jaccard)
            if not only_a and not only_b:
                identical_pairs += 1

            pairwise_rows.append(
                {
                    **pathway_meta,
                    "model_a": model_a,
                    "organism_a": models[model_a].get("organism", ""),
                    "model_b": model_b,
                    "organism_b": models[model_b].get("organism", ""),
                    "reaction_count_a": len(set_a),
                    "reaction_count_b": len(set_b),
                    "intersection_count": len(intersection),
                    "union_count": len(union),
                    "only_a_count": len(only_a),
                    "only_b_count": len(only_b),
                    "jaccard": round_float(jaccard),
                    "jaccard_percent": percent(jaccard),
                    "identical_reaction_set": int(not only_a and not only_b),
                }
            )

            if only_a or only_b:
                diff_rows.append(
                    {
                        **pathway_meta,
                        "model_a": model_a,
                        "model_b": model_b,
                        "only_a_count": len(only_a),
                        "only_a_reactions": pipe(only_a),
                        "only_b_count": len(only_b),
                        "only_b_reactions": pipe(only_b),
                        "shared_count": len(intersection),
                        "shared_reactions": pipe(intersection),
                    }
                )

        per_model_counts = [len(model_sets[model_id]) for model_id in model_ids]
        union_all = set().union(*model_sets.values()) if model_sets else set()
        core_all = set.intersection(*model_sets.values()) if model_sets else set()
        pair_count = len(jaccards)
        summary_rows.append(
            {
                **pathway_meta,
                "model_count": len(model_ids),
                "pair_count": pair_count,
                "identical_pair_count": identical_pairs,
                "identical_pair_percent": percent(identical_pairs / pair_count) if pair_count else 0,
                "mean_jaccard": round_float(mean(jaccards)),
                "median_jaccard": round_float(median(jaccards)),
                "min_jaccard": round_float(min(jaccards) if jaccards else 0),
                "max_jaccard": round_float(max(jaccards) if jaccards else 0),
                "mean_reaction_count": round_float(mean(per_model_counts), 2),
                "median_reaction_count": round_float(median(per_model_counts), 2),
                "min_reaction_count": min(per_model_counts) if per_model_counts else 0,
                "max_reaction_count": max(per_model_counts) if per_model_counts else 0,
                "union_reaction_count": len(union_all),
                "core_reaction_count": len(core_all),
                "variable_reaction_count": len(union_all - core_all),
                "core_reactions": pipe(core_all),
                "variable_reactions": pipe(union_all - core_all),
            }
        )

    return pairwise_rows, diff_rows, summary_rows


def build_frequency_table(
    reaction_sets: dict[str, dict[str, set[str]]],
    observed_bigg: dict[str, dict[str, set[str]]],
    models: dict[str, dict[str, str]],
    pathways: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows = []
    all_models = set(models)
    model_count = len(all_models)
    for pathway, model_sets in sorted(reaction_sets.items()):
        pathway_meta = pathways[pathway]
        union_all = set().union(*model_sets.values()) if model_sets else set()
        for reaction_id in sorted(union_all):
            present = {
                model_id
                for model_id, reaction_set in model_sets.items()
                if reaction_id in reaction_set
            }
            absent = all_models - present
            frequency = len(present) / model_count if model_count else 0.0
            rows.append(
                {
                    **pathway_meta,
                    "kegg_reaction_id": reaction_id,
                    "present_model_count": len(present),
                    "absent_model_count": len(absent),
                    "frequency_percent": percent(frequency),
                    "status": "core" if len(present) == model_count else "variable",
                    "model_reaction_ids_observed": pipe(observed_bigg[pathway][reaction_id]),
                    "present_models": pipe(present),
                    "absent_models": pipe(absent),
                }
            )
    return rows


def build_mapping_metric_tables(
    map_stats_rows: list[dict[str, str]],
    models: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected = [
        {**row, "model_id": row.get("bigg_id", "")}
        for row in map_stats_rows
        if row.get("bigg_id") in models and row.get("status") in {"built", "cached"}
    ]
    by_pathway = defaultdict(list)
    for row in selected:
        by_pathway[row["pathway"]].append(row)

    summary_rows = []
    for pathway, rows in sorted(by_pathway.items()):
        matched = [float(row["matched_reactions"]) for row in rows if row.get("matched_reactions") != ""]
        retention = [
            float(row["reaction_retention_percent"])
            for row in rows
            if row.get("reaction_retention_percent") != ""
        ]
        summary_rows.append(
            {
                "pathway": pathway,
                "pathway_rn": rows[0].get("pathway_rn", ""),
                "pathway_label": rows[0].get("pathway_label", ""),
                "model_count": len(rows),
                "mean_matched_reactions": round_float(mean(matched), 2),
                "median_matched_reactions": round_float(median(matched), 2),
                "min_matched_reactions": int(min(matched)) if matched else 0,
                "max_matched_reactions": int(max(matched)) if matched else 0,
                "mean_reaction_retention_percent": round_float(mean(retention), 2),
                "median_reaction_retention_percent": round_float(median(retention), 2),
                "min_reaction_retention_percent": round_float(min(retention), 2) if retention else 0,
                "max_reaction_retention_percent": round_float(max(retention), 2) if retention else 0,
            }
        )
    return selected, summary_rows


def write_readme(
    output_dir: Path,
    output_root: Path,
    model_count: int,
    *,
    scope: str,
    prefix: str,
    excluded_models: set[str],
) -> None:
    if scope == "ecoli":
        scope_text = "BiGG Escherichia coli models"
    else:
        scope_text = "BiGG prokaryotic models"
    lines = [
        "# Reaction Reproducibility Metrics",
        "",
        f"Source maps: `{output_root}`",
        f"Models: {model_count} {scope_text}; excluded: `{pipe(excluded_models)}`.",
        "",
        "Jaccard is calculated over KEGG reaction IDs that are actually present in each generated Escher JSON map.",
        "BiGG/model reaction IDs are retained in the long/frequency tables as supporting identifiers.",
        "",
        "Files:",
        f"- `{prefix}_map_reactions_long.tsv`: one row per drawn reaction per model-pathway map.",
        f"- `{prefix}_map_reaction_counts.tsv`: drawn KEGG reaction set and count per model-pathway.",
        f"- `{prefix}_pairwise_jaccard.tsv`: pairwise Jaccard metrics for every model pair within each pathway.",
        f"- `{prefix}_pairwise_reaction_differences.tsv`: reaction IDs unique to either model for non-identical pairs.",
        f"- `{prefix}_jaccard_summary_by_pathway.tsv`: compact Jaccard/count summary by pathway.",
        f"- `{prefix}_reaction_frequency_by_pathway.tsv`: core/variable reaction frequency across selected models.",
        f"- `{prefix}_mapping_metrics_by_model_pathway.tsv`: original BioEMMA mapping metrics subset for these models.",
        f"- `{prefix}_mapping_metric_summary_by_pathway.tsv`: mapping metric summary by pathway.",
    ]
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--scope",
        choices=sorted(DEFAULT_OUTPUT_DIRNAMES),
        default="ecoli",
        help="Model set to analyze. Inventory is already restricted to prokaryotic BiGG models.",
    )
    parser.add_argument(
        "--exclude-model",
        action="append",
        default=[],
        help="Model ID to exclude. Can be repeated. e_coli_core is always excluded.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    output_dir = args.output_dir or output_root / "stats" / DEFAULT_OUTPUT_DIRNAMES[args.scope]
    output_dir = output_dir.resolve()
    prefix = OUTPUT_PREFIXES[args.scope]
    excluded_models = set(args.exclude_model or set())
    excluded_models.add("e_coli_core")

    inventory_rows = read_tsv(output_root / "inventory" / "prokaryotic_models.tsv")
    map_stats_rows = read_tsv(output_root / "stats" / "map_stats.tsv")
    models = select_models(
        inventory_rows,
        scope=args.scope,
        excluded_models=excluded_models,
    )
    pathways = pathway_metadata(map_stats_rows)

    reaction_rows, count_rows, reaction_sets, observed_bigg = build_reaction_tables(
        output_root,
        models,
        pathways,
    )
    pairwise_rows, diff_rows, jaccard_summary_rows = build_pairwise_tables(
        reaction_sets,
        models,
        pathways,
    )
    frequency_rows = build_frequency_table(
        reaction_sets,
        observed_bigg,
        models,
        pathways,
    )
    mapping_rows, mapping_summary_rows = build_mapping_metric_tables(map_stats_rows, models)

    write_tsv(
        output_dir / f"{prefix}_map_reactions_long.tsv",
        reaction_rows,
        [
            "pathway",
            "pathway_rn",
            "pathway_label",
            "model_id",
            "organism",
            "reaction_node_id",
            "kegg_reaction_id",
            "model_reaction_id",
            "metabolite_count",
            "metabolite_bigg_ids",
            "map_json",
        ],
    )
    write_tsv(
        output_dir / f"{prefix}_map_reaction_counts.tsv",
        count_rows,
        [
            "pathway",
            "pathway_rn",
            "pathway_label",
            "model_id",
            "organism",
            "reaction_count",
            "reaction_set",
            "status",
            "map_json",
        ],
    )
    write_tsv(
        output_dir / f"{prefix}_pairwise_jaccard.tsv",
        pairwise_rows,
        [
            "pathway",
            "pathway_rn",
            "pathway_label",
            "model_a",
            "organism_a",
            "model_b",
            "organism_b",
            "reaction_count_a",
            "reaction_count_b",
            "intersection_count",
            "union_count",
            "only_a_count",
            "only_b_count",
            "jaccard",
            "jaccard_percent",
            "identical_reaction_set",
        ],
    )
    write_tsv(
        output_dir / f"{prefix}_pairwise_reaction_differences.tsv",
        diff_rows,
        [
            "pathway",
            "pathway_rn",
            "pathway_label",
            "model_a",
            "model_b",
            "only_a_count",
            "only_a_reactions",
            "only_b_count",
            "only_b_reactions",
            "shared_count",
            "shared_reactions",
        ],
    )
    write_tsv(
        output_dir / f"{prefix}_jaccard_summary_by_pathway.tsv",
        jaccard_summary_rows,
        [
            "pathway",
            "pathway_rn",
            "pathway_label",
            "model_count",
            "pair_count",
            "identical_pair_count",
            "identical_pair_percent",
            "mean_jaccard",
            "median_jaccard",
            "min_jaccard",
            "max_jaccard",
            "mean_reaction_count",
            "median_reaction_count",
            "min_reaction_count",
            "max_reaction_count",
            "union_reaction_count",
            "core_reaction_count",
            "variable_reaction_count",
            "core_reactions",
            "variable_reactions",
        ],
    )
    write_tsv(
        output_dir / f"{prefix}_reaction_frequency_by_pathway.tsv",
        frequency_rows,
        [
            "pathway",
            "pathway_rn",
            "pathway_label",
            "kegg_reaction_id",
            "present_model_count",
            "absent_model_count",
            "frequency_percent",
            "status",
            "model_reaction_ids_observed",
            "present_models",
            "absent_models",
        ],
    )
    write_tsv(
        output_dir / f"{prefix}_mapping_metrics_by_model_pathway.tsv",
        mapping_rows,
        [
            "pathway",
            "pathway_rn",
            "pathway_label",
            "model_id",
            "organism",
            "status",
            "model_reactions",
            "model_metabolites",
            "kegg_reactions",
            "kgml_reactions_omitted",
            "matched_reactions",
            "unmatched_reactions",
            "reaction_retention_percent",
            "matched_metabolites",
            "unmatched_metabolites",
            "metabolite_retention_percent",
            "map_json",
            "summary_json",
        ],
    )
    write_tsv(
        output_dir / f"{prefix}_mapping_metric_summary_by_pathway.tsv",
        mapping_summary_rows,
        [
            "pathway",
            "pathway_rn",
            "pathway_label",
            "model_count",
            "mean_matched_reactions",
            "median_matched_reactions",
            "min_matched_reactions",
            "max_matched_reactions",
            "mean_reaction_retention_percent",
            "median_reaction_retention_percent",
            "min_reaction_retention_percent",
            "max_reaction_retention_percent",
        ],
    )

    write_json(
        output_dir / "summary.json",
        {
            "source_output_root": str(output_root),
            "output_dir": str(output_dir),
            "scope": args.scope,
            "excluded_models": sorted(excluded_models),
            "model_count": len(models),
            "models": models,
            "pathways": pathways,
            "jaccard_summary_by_pathway": jaccard_summary_rows,
            "mapping_metric_summary_by_pathway": mapping_summary_rows,
            "files": sorted(path.name for path in output_dir.glob("*")),
        },
    )
    write_readme(
        output_dir,
        output_root,
        len(models),
        scope=args.scope,
        prefix=prefix,
        excluded_models=excluded_models,
    )
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
