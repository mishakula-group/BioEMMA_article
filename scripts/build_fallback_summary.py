from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bioemma.metanetx_mapper import MetaNetXMapper


ROOT = Path(__file__).parents[1]
FALLBACK_DIR = ROOT / "results" / "fallback"
OLD_RESOURCE = FALLBACK_DIR / "resources_0_4_1" / "reaction_mapping.tsv"
NEW_RESOURCE = FALLBACK_DIR / "resources_0_4_2" / "reaction_mapping.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_mapper(path: Path) -> MetaNetXMapper:
    return MetaNetXMapper(str(path), "first")


def fallback_sets(mapper: MetaNetXMapper) -> dict[str, set[str]]:
    bigg = {entry.kegg for entry in mapper.bigg_ec_fallback_entries()}
    seed = {entry.kegg for entry in mapper.seed_ec_fallback_entries()}
    return {
        "bigg": bigg,
        "seed": seed,
        "overlap": bigg & seed,
        "seed_only": seed - bigg,
        "bigg_only": bigg - seed,
    }


def get_mode(path: Path, mode: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data["results"]
    for row in data:
        if row["mode"] == mode:
            return row
    raise KeyError(mode)


def compact_mode(row: dict) -> dict[str, object]:
    reaction = row["reaction_level"]
    metrics = row["label_level_metrics"]
    return {
        "sources": row["sources"],
        "exact": reaction.get("exact"),
        "mixed_hit": reaction.get("mixed_hit"),
        "wrong_only": reaction.get("wrong_only"),
        "miss": reaction.get("miss"),
        "recovered_any": reaction.get("recovered_any"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "f1": metrics.get("f1"),
    }


def build_summary() -> dict[str, object]:
    old = load_mapper(OLD_RESOURCE)
    new = load_mapper(NEW_RESOURCE)
    old_stats = old.coverage_stats()
    new_stats = new.coverage_stats()
    sets = fallback_sets(new)

    seed_eval = FALLBACK_DIR / "evaluations" / "seed_fallback_eval" / "seed_fallback_confusion.json"
    bigg_eval = FALLBACK_DIR / "evaluations" / "ec_fallback_eval" / "ec_fallback_confusion.json"
    formula_eval = (
        FALLBACK_DIR
        / "evaluations"
        / "kegg_formula_eval"
        / "kegg_formula_fallback_confusion.json"
    )
    seed_formula_eval = (
        FALLBACK_DIR
        / "evaluations"
        / "seed_kegg_formula_eval"
        / "seed_kegg_formula_fallback_confusion.json"
    )
    map_comparison = json.loads(
        (FALLBACK_DIR / "map_nochange_evidence" / "regen_comparison.json").read_text(
            encoding="utf-8"
        )
    )

    return {
        "bioemma_version": "0.4.2",
        "old_resource": {
            "label": "BioEMMA 0.4.1 / BiGG EC fallback",
            "path": str(OLD_RESOURCE.relative_to(ROOT)),
            "sha256": sha256(OLD_RESOURCE),
            "coverage_stats": old_stats,
        },
        "new_resource": {
            "label": "BioEMMA 0.4.2 / BiGG + SEED EC fallback",
            "path": str(NEW_RESOURCE.relative_to(ROOT)),
            "sha256": sha256(NEW_RESOURCE),
            "coverage_stats": new_stats,
        },
        "resource_delta": {
            "total": new_stats["total"] - old_stats["total"],
            "has_bigg": new_stats["has_bigg"] - old_stats["has_bigg"],
            "has_seed": new_stats["has_seed"] - old_stats["has_seed"],
            "bigg_ec_fallback": new_stats["bigg_ec_fallback"]
            - old_stats.get("bigg_ec_fallback", old_stats.get("ec_fallback", 0)),
            "seed_ec_fallback": new_stats["seed_ec_fallback"]
            - old_stats.get("seed_ec_fallback", 0),
        },
        "fallback_overlap": {
            "bigg_ec_fallback": len(sets["bigg"]),
            "seed_ec_fallback": len(sets["seed"]),
            "overlap": len(sets["overlap"]),
            "seed_only": len(sets["seed_only"]),
            "bigg_only": len(sets["bigg_only"]),
            "overlap_percent_of_seed": len(sets["overlap"]) / len(sets["seed"]) * 100,
            "overlap_percent_of_bigg": len(sets["overlap"]) / len(sets["bigg"]) * 100,
        },
        "validation": {
            "bigg_mnx_participants_inclusive_best_ties": compact_mode(
                get_mode(bigg_eval, "inclusive_best_ties")
            ),
            "bigg_kegg_formula_inclusive_best_ties": compact_mode(
                get_mode(formula_eval, "kegg_formula_inclusive_best_ties")
            ),
            "seed_mnx_participants_inclusive_best_ties": compact_mode(
                get_mode(seed_eval, "inclusive_best_ties")
            ),
            "seed_mnx_participants_leave_one_mnx_out_best_ties": compact_mode(
                get_mode(seed_eval, "leave_one_mnx_out_best_ties")
            ),
            "seed_kegg_formula_inclusive_best_ties": compact_mode(
                get_mode(seed_formula_eval, "kegg_formula_inclusive_best_ties")
            ),
            "seed_kegg_formula_leave_one_mnx_out_best_ties": compact_mode(
                get_mode(seed_formula_eval, "kegg_formula_leave_one_mnx_out_best_ties")
            ),
        },
        "article_map_seed_fallback_delta": {
            "changed_maps": map_comparison.get("changed_maps", []),
            "changed_flux_json": map_comparison.get("changed_flux_json", []),
        },
    }


def pct(value: float) -> str:
    return f"{value:.1f}%"


def count_value(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        return len(value)
    return 0


def write_markdown(summary: dict[str, object]) -> None:
    old_stats = summary["old_resource"]["coverage_stats"]
    new_stats = summary["new_resource"]["coverage_stats"]
    delta = summary["resource_delta"]
    overlap = summary["fallback_overlap"]
    validation = summary["validation"]
    map_delta = summary["article_map_seed_fallback_delta"]

    lines = [
        "# BioEMMA 0.4.2 fallback summary",
        "",
        "BioEMMA 0.4.2 keeps the BiGG EC fallback from 0.4.1 and adds a separate SEED EC fallback layer.",
        "",
        "## Resource coverage",
        "",
        "| Metric | 0.4.1 | 0.4.2 | Delta |",
        "|---|---:|---:|---:|",
        f"| KEGG reaction rows | {old_stats['total']} | {new_stats['total']} | {delta['total']} |",
        f"| BiGG coverage | {old_stats['has_bigg']} | {new_stats['has_bigg']} | {delta['has_bigg']} |",
        f"| SEED coverage | {old_stats['has_seed']} | {new_stats['has_seed']} | {delta['has_seed']} |",
        f"| BiGG EC fallback rows | {old_stats.get('bigg_ec_fallback', old_stats.get('ec_fallback', 0))} | {new_stats['bigg_ec_fallback']} | {delta['bigg_ec_fallback']} |",
        f"| SEED EC fallback rows | {old_stats.get('seed_ec_fallback', 0)} | {new_stats['seed_ec_fallback']} | {delta['seed_ec_fallback']} |",
        "",
        "## Fallback overlap",
        "",
        f"- BiGG EC fallback reactions: `{overlap['bigg_ec_fallback']}`.",
        f"- SEED EC fallback reactions: `{overlap['seed_ec_fallback']}`.",
        f"- Overlap: `{overlap['overlap']}` reactions ({pct(overlap['overlap_percent_of_seed'])} of SEED fallback, {pct(overlap['overlap_percent_of_bigg'])} of BiGG fallback).",
        f"- SEED-only fallback reactions: `{overlap['seed_only']}`.",
        f"- BiGG-only fallback reactions: `{overlap['bigg_only']}`.",
        "",
        "## Validation snapshots",
        "",
        "| Test | Sources | Exact | Mixed hit | Wrong only | Miss | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    labels = [
        ("BiGG MNX participants inclusive best-ties", validation["bigg_mnx_participants_inclusive_best_ties"]),
        ("BiGG KEGG formula inclusive best-ties", validation["bigg_kegg_formula_inclusive_best_ties"]),
        ("SEED KEGG formula inclusive best-ties", validation["seed_kegg_formula_inclusive_best_ties"]),
        ("SEED KEGG formula leave-one-MNX-out best-ties", validation["seed_kegg_formula_leave_one_mnx_out_best_ties"]),
    ]
    for label, row in labels:
        lines.append(
            "| {label} | {sources} | {exact} | {mixed_hit} | {wrong_only} | {miss} | {precision:.3f} | {recall:.3f} | {f1:.3f} |".format(
                label=label,
                **row,
            )
        )

    lines.extend(
        [
            "",
            "## Article-map impact",
            "",
            f"- Fresh EC baseline vs SEED fallback changed maps: `{count_value(map_delta['changed_maps'])}`.",
            f"- Fresh EC baseline vs SEED fallback changed flux JSON files: `{count_value(map_delta['changed_flux_json'])}`.",
            "- Therefore article maps were copied from the 0.4.1 bundle instead of regenerated here.",
            "",
            "Source evidence is in `map_nochange_evidence/regen_comparison.md`.",
        ]
    )

    (FALLBACK_DIR / "fallback_summary.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    summary = build_summary()
    (FALLBACK_DIR / "fallback_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_markdown(summary)
    print(FALLBACK_DIR / "fallback_summary.md")
    print(FALLBACK_DIR / "fallback_summary.json")


if __name__ == "__main__":
    main()
