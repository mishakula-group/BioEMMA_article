from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


TABLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = TABLE_DIR.parents[1]
FIGURE_03_DIR = REPO_ROOT / "figures" / "figure_03"

PATHWAYS = ("map00010", "map00020", "map00030")
MODELS = {
    "gapseq": FIGURE_03_DIR / "inputs" / "gapseq.sbml.xml",
    "ModelSEED": FIGURE_03_DIR / "inputs" / "modelseed.sbml.xml",
    "Reconstructor": FIGURE_03_DIR / "inputs" / "reconstructor.sbml.xml",
}

README_PATH = TABLE_DIR / "README.md"
TSV_PATH = TABLE_DIR / "table_01.tsv"
DETAILS_TXT_PATH = TABLE_DIR / "table_01_reaction_details.txt"
DETAILS_JSON_PATH = TABLE_DIR / "table_01_reaction_details.json"
KGML_CACHE_DIR = TABLE_DIR / "kgml_cache"
COBRA_CACHE_DIR = TABLE_DIR / ".cobra_cache"


def configure_cobra_cache() -> None:
    COBRA_CACHE_DIR.mkdir(exist_ok=True)
    os.environ.setdefault("BIOEMMA_COBRA_CACHE_DIR", str(COBRA_CACHE_DIR))

    import appdirs

    original_user_cache_dir = appdirs.user_cache_dir

    def user_cache_dir(appname=None, appauthor=None, *args, **kwargs):
        if appname == "cobrapy" and appauthor == "opencobra":
            return str(COBRA_CACHE_DIR)
        return original_user_cache_dir(appname, appauthor, *args, **kwargs)

    appdirs.user_cache_dir = user_cache_dir


def normalize_to_rn(pathway: str) -> str:
    if pathway.startswith("map"):
        return "rn" + pathway[3:]
    return pathway


def split_kegg_ids(value: str | None, namespace: str) -> list[str]:
    ids = []
    prefix = f"{namespace}:"
    for token in (value or "").split():
        if token.startswith(prefix):
            ids.append(token.split(":", 1)[1])
        elif ":" not in token:
            ids.append(token)
    return ids


def fetch_kegg_reactions(pathway: str) -> dict[str, list[str]]:
    rn_pathway = normalize_to_rn(pathway)
    kgml_path = KGML_CACHE_DIR / f"{rn_pathway}.kgml"
    if kgml_path.exists():
        kgml_text = kgml_path.read_text(encoding="utf-8")
    else:
        url = f"https://rest.kegg.jp/get/{rn_pathway}/kgml"
        request = Request(url, headers={"User-Agent": "BioEMMA-table-01/1.0"})
        last_error = None
        for attempt in range(3):
            try:
                kgml_text = urlopen(request, timeout=30).read().decode("utf-8")
                KGML_CACHE_DIR.mkdir(exist_ok=True)
                kgml_path.write_text(kgml_text, encoding="utf-8")
                break
            except Exception as error:
                last_error = error
                time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError(f"Could not fetch KGML for {pathway}") from last_error

    root = ET.fromstring(kgml_text)

    all_reactions = []
    drawable_reactions = []
    reactions_without_coordinates = []

    for entry in root.findall("entry[@type='reaction']"):
        reactions = split_kegg_ids(entry.get("reaction"), "rn")
        graphics = entry.find("graphics")
        has_coordinates = (
            graphics is not None
            and graphics.get("x") is not None
            and graphics.get("y") is not None
        )

        for reaction in reactions:
            if reaction not in all_reactions:
                all_reactions.append(reaction)
            if has_coordinates:
                if reaction not in drawable_reactions:
                    drawable_reactions.append(reaction)
            elif reaction not in reactions_without_coordinates:
                reactions_without_coordinates.append(reaction)

    return {
        "all": all_reactions,
        "drawable": drawable_reactions,
        "without_coordinates": reactions_without_coordinates,
    }


def annotation_values(annotation: dict, key: str) -> list[str]:
    values = annotation.get(key, [])
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    elif not isinstance(values, (list, tuple, set)):
        values = [values]
    return [str(value) for value in values if value]


def model_reaction_annotations(model) -> list[dict[str, set[str]]]:
    annotations = []
    for reaction in model.reactions:
        annotations.append(
            {
                "kegg": set(annotation_values(reaction.annotation, "kegg.reaction")),
                "bigg": set(annotation_values(reaction.annotation, "bigg.reaction")),
                "seed": set(annotation_values(reaction.annotation, "seed.reaction")),
            }
        )
    return annotations


def retained_reactions(model_annotations, kegg_reactions, reaction_mapper) -> list[str]:
    retained = []
    for reaction in kegg_reactions:
        mapping = reaction_mapper.get(reaction)
        kegg_ids = {reaction}
        bigg_ids = set(mapping.bigg_all) if mapping else set()
        seed_ids = set(mapping.seed_all) if mapping else set()

        for annotation in model_annotations:
            if (
                kegg_ids & annotation["kegg"]
                or bigg_ids & annotation["bigg"]
                or seed_ids & annotation["seed"]
            ):
                retained.append(reaction)
                break
    return retained


def percent(count: int, total: int) -> str:
    return f"{count} ({count / total * 100:.1f}%)" if total else "0 (0.0%)"


def mapped_reactions(reactions: list[str], reaction_mapper) -> list[str]:
    mapped = []
    for reaction in reactions:
        mapping = reaction_mapper.get(reaction)
        if mapping and (mapping.bigg or mapping.seed):
            mapped.append(reaction)
    return mapped


def model_specific_counts(model_specific: dict[str, list[str]]) -> str:
    return str(sum(len(reactions) for reactions in model_specific.values()))


def build_rows(results: dict[str, dict]) -> list[list[str]]:
    return [
        ["KEGG pathway", *PATHWAYS],
        [
            "Reactions in KEGG map",
            *[str(len(results[pathway]["all_reactions"])) for pathway in PATHWAYS],
        ],
        [
            "Mapped reactions",
            *[
                (
                    f"{len(results[pathway]['mapped_reactions'])}/"
                    f"{len(results[pathway]['all_reactions'])} "
                    f"({len(results[pathway]['mapped_reactions']) / len(results[pathway]['all_reactions']) * 100:.1f}%)"
                )
                for pathway in PATHWAYS
            ],
        ],
        [
            "Retained in gapseq, n (% of KEGG map)",
            *[
                percent(
                    len(results[pathway]["retained"]["gapseq"]),
                    len(results[pathway]["all_reactions"]),
                )
                for pathway in PATHWAYS
            ],
        ],
        [
            "Retained in ModelSEED, n (% of KEGG map)",
            *[
                percent(
                    len(results[pathway]["retained"]["ModelSEED"]),
                    len(results[pathway]["all_reactions"]),
                )
                for pathway in PATHWAYS
            ],
        ],
        [
            "Retained in Reconstructor, n (% of KEGG map)",
            *[
                percent(
                    len(results[pathway]["retained"]["Reconstructor"]),
                    len(results[pathway]["all_reactions"]),
                )
                for pathway in PATHWAYS
            ],
        ],
        [
            "Reactions shared by all three models",
            *[str(len(results[pathway]["shared_by_all"])) for pathway in PATHWAYS],
        ],
        [
            "Model-specific reactions",
            *[
                model_specific_counts(results[pathway]["model_specific"])
                for pathway in PATHWAYS
            ],
        ],
    ]


def write_tsv(rows: list[list[str]]) -> None:
    lines = ["Row\tmap00010\tmap00020\tmap00030"]
    lines.extend("\t".join(row) for row in rows)
    TSV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(rows: list[list[str]]) -> None:
    lines = [
        "# Table 1. Retention of KEGG map reactions in reconstructions",
        "",
        "| Row | map00010 | map00020 | map00030 |",
        "|---|---:|---:|---:|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.extend(
        [
            "",
            "Notes:",
            "",
            "- Mapped reactions are KEGG map reactions for which BioEMMA/MetaNetX provides at least one supported BiGG or SEED identifier.",
            "- Retained reactions are mapped KEGG reactions that can be matched to the corresponding SBML reconstruction through KEGG, BiGG, or SEED annotations and remain in the model-filtered map.",
            "- BioEMMA normalizes `map00010` to `rn00010` internally; the table keeps the user-facing `map00010` label.",
            "- KGML for `map00030` contains one reaction without coordinates (`R06837`). It is counted in KEGG and mapped totals but cannot be retained on a drawable BioEMMA map.",
            "- Detailed shared and model-specific reaction lists are written to `table_01_reaction_details.txt` and `table_01_reaction_details.json`.",
        ]
    )
    README_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_details(results: dict[str, dict]) -> None:
    lines = []
    for pathway in PATHWAYS:
        data = results[pathway]
        lines.append(pathway)
        if data["reactions_without_coordinates"]:
            lines.append(
                "  Reactions without KGML coordinates: "
                + ", ".join(data["reactions_without_coordinates"])
            )
        lines.append(
            "  Shared by all three models: "
            + (", ".join(data["shared_by_all"]) or "none")
        )
        lines.append("  Model-specific reactions:")
        for model, reactions in data["model_specific"].items():
            lines.append(f"    {model}: " + (", ".join(reactions) or "none"))
        lines.append("")

    DETAILS_TXT_PATH.write_text("\n".join(lines), encoding="utf-8")
    DETAILS_JSON_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    configure_cobra_cache()

    import cobra
    from bioemma._resources import resource_path
    from bioemma.metanetx_mapper import MetaNetXMapper

    reaction_mapper = MetaNetXMapper(resource_path("reaction_mapping.tsv"), "first")
    loaded_models = {
        name: cobra.io.read_sbml_model(str(path)) for name, path in MODELS.items()
    }
    annotations = {
        name: model_reaction_annotations(model) for name, model in loaded_models.items()
    }

    results = {}
    for pathway in PATHWAYS:
        kegg_reactions = fetch_kegg_reactions(pathway)
        all_reactions = kegg_reactions["all"]
        drawable_reactions = kegg_reactions["drawable"]
        retained = {
            model: retained_reactions(
                model_annotations,
                drawable_reactions,
                reaction_mapper,
            )
            for model, model_annotations in annotations.items()
        }

        retained_sets = [set(reactions) for reactions in retained.values()]
        shared_by_all = sorted(set.intersection(*retained_sets))
        model_specific = {
            model: sorted(
                set(reactions)
                - set().union(
                    *[
                        set(other_reactions)
                        for other_model, other_reactions in retained.items()
                        if other_model != model
                    ]
                )
            )
            for model, reactions in retained.items()
        }

        results[pathway] = {
            "all_reactions": all_reactions,
            "drawable_reactions": drawable_reactions,
            "reactions_without_coordinates": kegg_reactions["without_coordinates"],
            "mapped_reactions": mapped_reactions(all_reactions, reaction_mapper),
            "retained": retained,
            "shared_by_all": shared_by_all,
            "model_specific": model_specific,
        }

    rows = build_rows(results)
    write_tsv(rows)
    write_readme(rows)
    write_details(results)

    print(f"Wrote {README_PATH}")
    print(f"Wrote {TSV_PATH}")
    print(f"Wrote {DETAILS_TXT_PATH}")
    print(f"Wrote {DETAILS_JSON_PATH}")


if __name__ == "__main__":
    main()
