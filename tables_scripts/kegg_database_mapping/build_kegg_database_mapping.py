from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from bioemma._resources import resource_path
from bioemma.metanetx_mapper import MetaNetXMapper


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
INPUT_PATH = REPO_ROOT / "data" / "kegg_pathways.tsv"
OUTPUT_DIR = REPO_ROOT / "results" / "table_02_kegg_database_mapping"


def split_reactions(value: str | None) -> list[str]:
    reactions = []
    seen = set()
    for item in (value or "").split("|"):
        reaction = item.strip()
        if not reaction or reaction in seen:
            continue
        reactions.append(reaction)
        seen.add(reaction)
    return reactions


def mapping_sets(
    reactions: list[str],
    reaction_mapper: MetaNetXMapper,
) -> dict[str, list[str]]:
    bigg = []
    seed = []
    neither = []

    for reaction in reactions:
        mapping = reaction_mapper.get(reaction)
        has_bigg = bool(mapping and set(mapping.bigg_all))
        has_seed = bool(mapping and set(mapping.seed_all))

        if has_bigg:
            bigg.append(reaction)
        if has_seed:
            seed.append(reaction)
        if not has_bigg and not has_seed:
            neither.append(reaction)

    bigg_set = set(bigg)
    seed_set = set(seed)
    return {
        "bigg_mapped": bigg,
        "seed_mapped": seed,
        "both_bigg_and_seed": sorted(bigg_set & seed_set),
        "either_bigg_or_seed": sorted(bigg_set | seed_set),
        "unmapped_to_bigg_or_seed": neither,
    }


def percent(count: int, total: int) -> str:
    return f"{count / total * 100:.1f}%" if total else "0.0%"


def count_row(row: dict[str, str], reaction_mapper: MetaNetXMapper) -> dict[str, Any]:
    reactions = split_reactions(row.get("Reactions"))
    mapped = mapping_sets(reactions, reaction_mapper)
    total = len(reactions)

    return {
        "source": row.get("Source", ""),
        "pathway_id": row.get("Source ID", ""),
        "pathway_name": row.get("Name", ""),
        "category": row.get("Aliases", ""),
        "kegg_reactions": total,
        "seed_mapped": len(mapped["seed_mapped"]),
        "bigg_mapped": len(mapped["bigg_mapped"]),
        "both_bigg_and_seed": len(mapped["both_bigg_and_seed"]),
        "either_bigg_or_seed": len(mapped["either_bigg_or_seed"]),
        "unmapped_to_bigg_or_seed": len(mapped["unmapped_to_bigg_or_seed"]),
        "seed_mapped_percent": percent(len(mapped["seed_mapped"]), total),
        "bigg_mapped_percent": percent(len(mapped["bigg_mapped"]), total),
        "either_mapped_percent": percent(len(mapped["either_bigg_or_seed"]), total),
        "details": {
            "reactions": reactions,
            **mapped,
        },
    }


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "pathway_id",
        "pathway_name",
        "category",
        "kegg_reactions",
        "seed_mapped",
        "bigg_mapped",
        "both_bigg_and_seed",
        "either_bigg_or_seed",
        "unmapped_to_bigg_or_seed",
        "seed_mapped_percent",
        "bigg_mapped_percent",
        "either_mapped_percent",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# KEGG reaction mappings to SEED and BiGG",
        "",
        "Counts are based on the reaction lists in `data/kegg_pathways.tsv` and BioEMMA/MetaNetX reaction mappings.",
        "No KEGG downloads are performed by this table build.",
        "",
        "| Pathway | Name | KEGG reactions | SEED matched | BiGG matched | Either | Unmatched |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["pathway_id"],
                    row["pathway_name"].replace("|", "\\|"),
                    str(row["kegg_reactions"]),
                    str(row["seed_mapped"]),
                    str(row["bigg_mapped"]),
                    str(row["either_bigg_or_seed"]),
                    str(row["unmapped_to_bigg_or_seed"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "`Either` is the number of KEGG reactions mapped to at least one supported database identifier: SEED or BiGG.",
            "It is a union, not `SEED + BiGG`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")

    reaction_mapper = MetaNetXMapper(resource_path("reaction_mapping.tsv"), "first")
    with INPUT_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = [
            count_row(row, reaction_mapper)
            for row in csv.DictReader(file, delimiter="\t")
            if row.get("Source ID", "").startswith("map")
        ]
    rows = [row for row in rows if row["kegg_reactions"] > 0]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_tsv(OUTPUT_DIR / "kegg_database_mapping_all_pathways.tsv", rows)
    write_markdown(OUTPUT_DIR / "kegg_database_mapping_all_pathways.md", rows)
    (OUTPUT_DIR / "kegg_database_mapping_all_pathways.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"pathways: {len(rows)}")
    print(f"tsv: {OUTPUT_DIR / 'kegg_database_mapping_all_pathways.tsv'}")
    print(f"markdown: {OUTPUT_DIR / 'kegg_database_mapping_all_pathways.md'}")
    print(f"json: {OUTPUT_DIR / 'kegg_database_mapping_all_pathways.json'}")


if __name__ == "__main__":
    main()
