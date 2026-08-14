from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import requests
from bioemma._resources import resource_path
from bioemma.metanetx_mapper import MetaNetXMapper
from bioemma.workflow import build_outputs, validate_escher_map


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "bigg_prokaryote_bioemma"

BIGG_API_MODELS_URL = "http://bigg.ucsd.edu/api/v2/models"
BIGG_STATIC_MODEL_URL = "http://bigg.ucsd.edu/static/models/{model_id}.xml"
KEGG_KGML_URL = "http://rest.kegg.jp/get/{pathway}/kgml"
USER_AGENT = "BioEMMA-article-BiGG-prokaryote-batch/1.0"

DATABASE = "BIGG"
SEED_ID_PATTERN = re.compile(r"^(cpd\d+)(?:_([A-Za-z]\d*|[a-z]))?$")
MANUAL_SEED_TO_BIGG = {
    "cpd00001": "h2o",
    "cpd00009": "pi",
    "cpd00102": "g3p",
    "cpd00260": "icit",
}

EUKARYOTIC_ORGANISM_PREFIXES = (
    "Chlamydomonas ",
    "Cricetulus ",
    "Homo ",
    "Mus ",
    "Phaeodactylum ",
    "Plasmodium ",
    "Saccharomyces ",
    "Trypanosoma ",
)

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
class PathwaySpec:
    slug: str
    rn_id: str
    label: str


PATHWAYS = (
    PathwaySpec("map00010", "rn00010", "Glycolysis / gluconeogenesis"),
    PathwaySpec("map00020", "rn00020", "Citrate cycle (TCA cycle)"),
    PathwaySpec("map00030", "rn00030", "Pentose phosphate pathway"),
    PathwaySpec("map00680", "rn00680", "Methane metabolism / C1 metabolism"),
)

PATHWAY_ALIASES = {
    "glycolysis": "rn00010",
    "map00010": "rn00010",
    "00010": "rn00010",
    "rn00010": "rn00010",
    "tca": "rn00020",
    "citrate": "rn00020",
    "map00020": "rn00020",
    "00020": "rn00020",
    "rn00020": "rn00020",
    "ppp": "rn00030",
    "pentose": "rn00030",
    "map00030": "rn00030",
    "00030": "rn00030",
    "rn00030": "rn00030",
    "c1": "rn00680",
    "methane": "rn00680",
    "methane_metabolism": "rn00680",
    "map00680": "rn00680",
    "00680": "rn00680",
    "rn00680": "rn00680",
}

MAP_STATS_FIELDS = (
    "status",
    "bigg_id",
    "organism",
    "pathway",
    "pathway_rn",
    "pathway_label",
    "source_reaction_count",
    "source_metabolite_count",
    "source_gene_count",
    "model_reactions",
    "model_metabolites",
    "kegg_reactions",
    "kegg_metabolites",
    "kgml_reaction_entries_omitted",
    "kgml_reactions_omitted",
    "matched_reactions",
    "unmatched_reactions",
    "reaction_retention_percent",
    "matched_metabolites",
    "unmatched_metabolites",
    "metabolite_retention_percent",
    "escher_nodes",
    "escher_reactions",
    "escher_segments",
    "invalid_segments_removed",
    "secondary_nodes_seen",
    "secondary_nodes_converted",
    "map_json",
    "map_html",
    "summary_json",
    "model_xml",
    "elapsed_seconds",
    "error",
)

INVENTORY_FIELDS = (
    "bigg_id",
    "organism",
    "reaction_count",
    "metabolite_count",
    "gene_count",
    "domain_classification",
    "classification_reason",
)


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(path: Path | str | None) -> str:
    if path is None:
        return ""
    path = Path(path)
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def request_with_retries(
    session: requests.Session,
    url: str,
    *,
    timeout: int = 60,
    retries: int = 4,
    stream: bool = False,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout, stream=stream)
            response.raise_for_status()
            return response
        except Exception as error:
            last_error = error
            if attempt == retries:
                break
            time.sleep(min(20, 2 * attempt))
    raise RuntimeError(f"Request failed after {retries} attempts: {url}") from last_error


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def normalize_pathway(value: str) -> PathwaySpec:
    key = value.strip().lower()
    rn_id = PATHWAY_ALIASES.get(key)
    if rn_id is None:
        if key.startswith("map") and key[3:].isdigit():
            rn_id = f"rn{key[3:]}"
        elif key.startswith("rn") and key[2:].isdigit():
            rn_id = key
        elif key.isdigit():
            rn_id = f"rn{key.zfill(5)}"
        else:
            raise ValueError(f"Unsupported pathway value: {value}")

    for spec in PATHWAYS:
        if spec.rn_id == rn_id:
            return spec
    return PathwaySpec(f"map{rn_id[2:]}", rn_id, rn_id)


def classify_domain(model_meta: dict[str, Any]) -> tuple[str, str]:
    organism = str(model_meta.get("organism") or "")
    for prefix in EUKARYOTIC_ORGANISM_PREFIXES:
        if organism.startswith(prefix):
            return "eukaryote_excluded", f"organism starts with {prefix.strip()}"
    return "prokaryote_selected", "not in known eukaryotic BiGG taxa"


def load_bigg_inventory(
    session: requests.Session,
    output_root: Path,
    *,
    force: bool,
) -> list[dict[str, Any]]:
    api_json_path = output_root / "inventory" / "bigg_models_api_results.json"
    if api_json_path.exists() and not force:
        payload = read_json(api_json_path)
    else:
        log("Downloading BiGG model inventory")
        payload = request_with_retries(session, BIGG_API_MODELS_URL).json()
        write_json(
            api_json_path,
            {
                "source_url": BIGG_API_MODELS_URL,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                **payload,
            },
        )

    models = list(payload["results"])
    models.sort(key=lambda item: str(item.get("bigg_id", "")).lower())
    return models


def inventory_rows(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for model in models:
        classification, reason = classify_domain(model)
        rows.append(
            {
                "bigg_id": model.get("bigg_id"),
                "organism": model.get("organism"),
                "reaction_count": model.get("reaction_count"),
                "metabolite_count": model.get("metabolite_count"),
                "gene_count": model.get("gene_count"),
                "domain_classification": classification,
                "classification_reason": reason,
            }
        )
    return rows


def select_models(
    models: list[dict[str, Any]],
    *,
    model_filter: set[str] | None,
    limit: int | None,
    include_eukaryotes: bool,
) -> list[dict[str, Any]]:
    selected = []
    known_ids = {str(model.get("bigg_id")) for model in models}
    if model_filter:
        missing = sorted(model_filter - known_ids)
        if missing:
            raise ValueError("Unknown BiGG model IDs: " + ", ".join(missing))

    for model in models:
        bigg_id = str(model.get("bigg_id"))
        classification, _reason = classify_domain(model)
        if model_filter and bigg_id not in model_filter:
            continue
        if not include_eukaryotes and classification != "prokaryote_selected":
            continue
        selected.append(model)

    if limit is not None:
        selected = selected[:limit]
    return selected


def ensure_kgml(
    session: requests.Session,
    pathway: PathwaySpec,
    kgml_dir: Path,
    *,
    force: bool,
) -> Path:
    kgml_path = kgml_dir / f"{pathway.rn_id}.kgml"
    if kgml_path.exists() and kgml_path.stat().st_size > 0 and not force:
        return kgml_path

    url = KEGG_KGML_URL.format(pathway=pathway.rn_id)
    log(f"Downloading KEGG KGML for {pathway.slug} ({pathway.label})")
    response = request_with_retries(session, url, timeout=60)
    kgml_path.parent.mkdir(parents=True, exist_ok=True)
    kgml_path.write_text(response.text, encoding="utf-8")
    return kgml_path


def split_kegg_reaction_ids(value: str | None) -> list[str]:
    reaction_ids = []
    for token in (value or "").split():
        if token.startswith("rn:"):
            reaction_ids.append(token.split(":", 1)[1])
        elif token:
            reaction_ids.append(token)
    return reaction_ids


def sanitize_kgml_for_bioemma(
    kgml_path: Path,
    *,
    force: bool,
) -> tuple[Path, dict[str, Any]]:
    drawable_path = kgml_path.with_name(f"{kgml_path.stem}.drawable.kgml")
    metadata_path = kgml_path.with_name(f"{kgml_path.stem}.drawable_sanitization.json")
    if drawable_path.exists() and metadata_path.exists() and not force:
        return drawable_path, read_json(metadata_path)

    tree = ET.parse(kgml_path)
    root = tree.getroot()
    removed_entries = []
    for entry in list(root.findall("entry")):
        if entry.get("type") != "reaction":
            continue
        graphics = entry.find("graphics")
        if (
            graphics is not None
            and graphics.get("x") is not None
            and graphics.get("y") is not None
        ):
            continue
        removed_entries.append(
            {
                "entry_id": entry.get("id"),
                "name": entry.get("name"),
                "reaction": entry.get("reaction"),
                "reaction_ids": split_kegg_reaction_ids(entry.get("reaction")),
            }
        )
        root.remove(entry)

    drawable_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(drawable_path, encoding="utf-8", xml_declaration=True)
    metadata = {
        "source_kgml": str(kgml_path),
        "drawable_kgml": str(drawable_path),
        "removed_reaction_entries": removed_entries,
        "removed_reaction_entry_count": len(removed_entries),
        "removed_reaction_ids": sorted(
            {
                reaction_id
                for entry in removed_entries
                for reaction_id in entry["reaction_ids"]
            }
        ),
    }
    write_json(metadata_path, metadata)
    return drawable_path, metadata


def ensure_model_xml(
    session: requests.Session,
    model_meta: dict[str, Any],
    models_dir: Path,
    *,
    force: bool,
) -> tuple[Path, str]:
    model_id = str(model_meta["bigg_id"])
    model_path = models_dir / f"{model_id}.xml"
    if model_path.exists() and model_path.stat().st_size > 0 and not force:
        return model_path, "cached"

    url = BIGG_STATIC_MODEL_URL.format(model_id=model_id)
    log(f"Downloading {model_id}")
    response = request_with_retries(session, url, timeout=180, stream=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    part_path = model_path.with_suffix(".xml.part")
    with part_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)
    if part_path.stat().st_size == 0:
        raise RuntimeError(f"Downloaded empty model file for {model_id}")
    part_path.replace(model_path)
    return model_path, "downloaded"


def configure_cobra_cache(cache_dir: Path) -> None:
    os.environ.setdefault("BIOEMMA_COBRA_CACHE_DIR", str(cache_dir))
    cache_dir.mkdir(parents=True, exist_ok=True)

    import appdirs

    original_user_cache_dir = appdirs.user_cache_dir

    def user_cache_dir(appname=None, appauthor=None, *args, **kwargs):
        if appname == "cobrapy" and appauthor == "opencobra":
            return str(cache_dir)
        return original_user_cache_dir(appname, appauthor, *args, **kwargs)

    appdirs.user_cache_dir = user_cache_dir


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


def save_html(path: Path, map_json_path: Path) -> None:
    import escher

    path.parent.mkdir(parents=True, exist_ok=True)
    escher.Builder(map_json=str(map_json_path)).save_html(str(path))


def rename_map(
    escher_map: list[dict[str, Any]],
    *,
    model_id: str,
    organism: str,
    pathway: PathwaySpec,
) -> None:
    escher_map[0]["map_name"] = f"bigg_{model_id}_{pathway.slug}_model_reconstruction"
    escher_map[0]["map_id"] = f"{model_id}_{pathway.slug}_model_reconstruction"
    escher_map[0]["map_description"] = (
        f"BiGG model {model_id} ({organism}) mapped to KEGG {pathway.rn_id}; "
        "model-filtered BioEMMA pathway layout."
    )


def ratio_percent(numerator: Any, denominator: Any) -> float:
    try:
        denominator = float(denominator)
        numerator = float(numerator)
    except (TypeError, ValueError):
        return 0.0
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100.0, 2)


def stats_row(
    *,
    status: str,
    model_meta: dict[str, Any],
    model_xml: Path | None,
    pathway: PathwaySpec,
    map_json: Path | None = None,
    map_html: Path | None = None,
    summary_json: Path | None = None,
    summary: dict[str, Any] | None = None,
    elapsed_seconds: float | None = None,
    error: str = "",
) -> dict[str, Any]:
    model_summary = (summary or {}).get("model", {})
    kegg = (summary or {}).get("kegg", {})
    matching = (summary or {}).get("map_stats", {}).get("model_matching", {})
    escher = (summary or {}).get("escher", {})
    batch = (summary or {}).get("bigg_batch", {})
    segment_cleanup = batch.get("invalid_segment_cleanup", {})
    secondary_normalization = batch.get("secondary_metabolite_bigg_normalization", {})
    kgml_sanitization = batch.get("kgml_sanitization", {})
    matched_reactions = matching.get("matched_reactions", "")
    kegg_reactions = kegg.get("reactions", "")
    matched_metabolites = matching.get("matched_metabolites", "")
    kegg_metabolites = kegg.get("metabolites", "")

    return {
        "status": status,
        "bigg_id": model_meta.get("bigg_id", ""),
        "organism": model_meta.get("organism", ""),
        "pathway": pathway.slug,
        "pathway_rn": pathway.rn_id,
        "pathway_label": pathway.label,
        "source_reaction_count": model_meta.get("reaction_count", ""),
        "source_metabolite_count": model_meta.get("metabolite_count", ""),
        "source_gene_count": model_meta.get("gene_count", ""),
        "model_reactions": model_summary.get("reactions", ""),
        "model_metabolites": model_summary.get("metabolites", ""),
        "kegg_reactions": kegg_reactions,
        "kegg_metabolites": kegg_metabolites,
        "kgml_reaction_entries_omitted": kgml_sanitization.get(
            "removed_reaction_entry_count", ""
        ),
        "kgml_reactions_omitted": ", ".join(
            kgml_sanitization.get("removed_reaction_ids", [])
        ),
        "matched_reactions": matched_reactions,
        "unmatched_reactions": matching.get("unmatched_reactions", ""),
        "reaction_retention_percent": ratio_percent(matched_reactions, kegg_reactions),
        "matched_metabolites": matched_metabolites,
        "unmatched_metabolites": matching.get("unmatched_metabolites", ""),
        "metabolite_retention_percent": ratio_percent(
            matched_metabolites, kegg_metabolites
        ),
        "escher_nodes": escher.get("nodes", ""),
        "escher_reactions": escher.get("reactions", ""),
        "escher_segments": escher.get("segments", ""),
        "invalid_segments_removed": segment_cleanup.get("segments_removed", ""),
        "secondary_nodes_seen": secondary_normalization.get("secondary_nodes_seen", ""),
        "secondary_nodes_converted": secondary_normalization.get(
            "secondary_nodes_converted", ""
        ),
        "map_json": rel(map_json),
        "map_html": rel(map_html),
        "summary_json": rel(summary_json),
        "model_xml": rel(model_xml),
        "elapsed_seconds": "" if elapsed_seconds is None else round(elapsed_seconds, 3),
        "error": error,
    }


def build_one_map(
    *,
    cobra_model: Any,
    model_meta: dict[str, Any],
    model_xml: Path,
    pathway: PathwaySpec,
    kgml_path: Path,
    kgml_sanitization: dict[str, Any],
    output_root: Path,
    metabolite_mapper: MetaNetXMapper,
    force_maps: bool,
    save_html_files: bool,
) -> dict[str, Any]:
    model_id = str(model_meta["bigg_id"])
    map_dir = output_root / "maps" / pathway.slug / model_id
    map_json_path = map_dir / f"{model_id}_{pathway.slug}_map.json"
    map_html_path = map_dir / f"{model_id}_{pathway.slug}_map.html"
    summary_path = map_dir / "summary.json"
    error_path = map_dir / "error.json"

    has_outputs = summary_path.exists() and map_json_path.exists()
    if save_html_files:
        has_outputs = has_outputs and map_html_path.exists()
    if has_outputs and not force_maps:
        summary = read_json(summary_path)
        return stats_row(
            status="cached",
            model_meta=model_meta,
            model_xml=model_xml,
            pathway=pathway,
            map_json=map_json_path,
            map_html=map_html_path if save_html_files else None,
            summary_json=summary_path,
            summary=summary,
        )

    started_at = time.perf_counter()
    result = build_outputs(
        model=cobra_model,
        kgml=kgml_path,
        database=DATABASE,
        visualization_options=VISUALIZATION_OPTIONS,
        include_kegg_only=False,
        use_database_secondary_metabolite_ids=True,
        save_kegg_map=False,
        save_html=False,
    )

    rename_map(
        result.escher_map,
        model_id=model_id,
        organism=str(model_meta.get("organism") or ""),
        pathway=pathway,
    )
    normalization_stats = normalize_secondary_metabolite_ids(
        result.escher_map,
        metabolite_mapper,
    )
    segment_cleanup_stats = remove_invalid_segments(result.escher_map)
    validation = validate_escher_map(result.escher_map)

    write_json(map_json_path, result.escher_map)
    if save_html_files:
        save_html(map_html_path, map_json_path)

    summary = dict(result.summary)
    summary["escher"] = validation
    summary["paths"] = {
        "map_json": str(map_json_path),
        "map_html": str(map_html_path) if save_html_files else "",
        "summary_json": str(summary_path),
        "model_xml": str(model_xml),
        "kgml": str(kgml_path),
    }
    summary["bigg_batch"] = {
        "bigg_id": model_id,
        "organism": model_meta.get("organism", ""),
        "source_counts": {
            "reactions": model_meta.get("reaction_count", ""),
            "metabolites": model_meta.get("metabolite_count", ""),
            "genes": model_meta.get("gene_count", ""),
        },
        "pathway": pathway.slug,
        "pathway_rn": pathway.rn_id,
        "pathway_label": pathway.label,
        "database": DATABASE,
        "include_kegg_only": False,
        "secondary_metabolite_bigg_normalization": normalization_stats,
        "invalid_segment_cleanup": segment_cleanup_stats,
        "kgml_sanitization": kgml_sanitization,
    }
    write_json(summary_path, summary)
    if error_path.exists():
        error_path.unlink()

    return stats_row(
        status="built",
        model_meta=model_meta,
        model_xml=model_xml,
        pathway=pathway,
        map_json=map_json_path,
        map_html=map_html_path if save_html_files else None,
        summary_json=summary_path,
        summary=summary,
        elapsed_seconds=time.perf_counter() - started_at,
    )


def write_map_stats(output_root: Path, rows: list[dict[str, Any]]) -> None:
    write_tsv(output_root / "stats" / "map_stats.tsv", rows, MAP_STATS_FIELDS)
    write_json(output_root / "stats" / "map_stats.json", rows)


def successful_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("status") in {"built", "cached"}]


def aggregate_pathway_stats(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregated = []
    for pathway in PATHWAYS:
        pathway_rows = [row for row in rows if row.get("pathway") == pathway.slug]
        ok_rows = [row for row in pathway_rows if row.get("status") in {"built", "cached"}]
        retention = [
            float(row["reaction_retention_percent"])
            for row in ok_rows
            if row.get("reaction_retention_percent") != ""
        ]
        matched = [
            int(row["matched_reactions"])
            for row in ok_rows
            if str(row.get("matched_reactions", "")).isdigit()
        ]
        aggregated.append(
            {
                "pathway": pathway.slug,
                "pathway_rn": pathway.rn_id,
                "pathway_label": pathway.label,
                "models_attempted": len(pathway_rows),
                "models_successful": len(ok_rows),
                "models_failed": len(pathway_rows) - len(ok_rows),
                "models_with_zero_matched_reactions": sum(
                    1 for value in matched if value == 0
                ),
                "mean_reaction_retention_percent": (
                    round(statistics.fmean(retention), 2) if retention else ""
                ),
                "median_reaction_retention_percent": (
                    round(statistics.median(retention), 2) if retention else ""
                ),
                "min_reaction_retention_percent": min(retention) if retention else "",
                "max_reaction_retention_percent": max(retention) if retention else "",
                "mean_matched_reactions": (
                    round(statistics.fmean(matched), 2) if matched else ""
                ),
                "median_matched_reactions": (
                    round(statistics.median(matched), 2) if matched else ""
                ),
            }
        )
    return aggregated


def aggregate_model_stats(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_model: dict[str, list[dict[str, Any]]] = {}
    for row in successful_rows(rows):
        by_model.setdefault(str(row["bigg_id"]), []).append(row)

    model_rows = []
    for model_id, model_rows_for_id in sorted(by_model.items()):
        first = model_rows_for_id[0]
        output = {
            "bigg_id": model_id,
            "organism": first.get("organism", ""),
            "successful_pathways": len(model_rows_for_id),
            "mean_reaction_retention_percent": round(
                statistics.fmean(
                    float(row["reaction_retention_percent"])
                    for row in model_rows_for_id
                    if row.get("reaction_retention_percent") != ""
                ),
                2,
            ),
        }
        for pathway in PATHWAYS:
            row = next(
                (
                    item
                    for item in model_rows_for_id
                    if item.get("pathway") == pathway.slug
                ),
                None,
            )
            output[f"{pathway.slug}_matched_reactions"] = (
                "" if row is None else row.get("matched_reactions", "")
            )
            output[f"{pathway.slug}_reaction_retention_percent"] = (
                "" if row is None else row.get("reaction_retention_percent", "")
            )
        model_rows.append(output)
    return model_rows


def write_aggregates(output_root: Path, rows: list[dict[str, Any]]) -> None:
    pathway_rows = aggregate_pathway_stats(rows)
    pathway_fields = (
        "pathway",
        "pathway_rn",
        "pathway_label",
        "models_attempted",
        "models_successful",
        "models_failed",
        "models_with_zero_matched_reactions",
        "mean_reaction_retention_percent",
        "median_reaction_retention_percent",
        "min_reaction_retention_percent",
        "max_reaction_retention_percent",
        "mean_matched_reactions",
        "median_matched_reactions",
    )
    write_tsv(output_root / "stats" / "pathway_stats.tsv", pathway_rows, pathway_fields)
    write_json(output_root / "stats" / "pathway_stats.json", pathway_rows)

    model_rows = aggregate_model_stats(rows)
    model_fields = (
        "bigg_id",
        "organism",
        "successful_pathways",
        "mean_reaction_retention_percent",
        *[
            field
            for pathway in PATHWAYS
            for field in (
                f"{pathway.slug}_matched_reactions",
                f"{pathway.slug}_reaction_retention_percent",
            )
        ],
    )
    write_tsv(output_root / "stats" / "model_stats.tsv", model_rows, model_fields)
    write_json(output_root / "stats" / "model_stats.json", model_rows)

    top_rows = []
    for pathway in PATHWAYS:
        pathway_rows_ok = [
            row
            for row in successful_rows(rows)
            if row.get("pathway") == pathway.slug
        ]
        pathway_rows_ok.sort(
            key=lambda row: (
                float(row.get("reaction_retention_percent") or 0.0),
                int(row.get("matched_reactions") or 0),
            ),
            reverse=True,
        )
        for rank, row in enumerate(pathway_rows_ok[:15], start=1):
            top_rows.append(
                {
                    "pathway": pathway.slug,
                    "rank": rank,
                    "bigg_id": row.get("bigg_id", ""),
                    "organism": row.get("organism", ""),
                    "matched_reactions": row.get("matched_reactions", ""),
                    "kegg_reactions": row.get("kegg_reactions", ""),
                    "reaction_retention_percent": row.get(
                        "reaction_retention_percent", ""
                    ),
                    "map_html": row.get("map_html", ""),
                }
            )
    top_fields = (
        "pathway",
        "rank",
        "bigg_id",
        "organism",
        "matched_reactions",
        "kegg_reactions",
        "reaction_retention_percent",
        "map_html",
    )
    write_tsv(output_root / "stats" / "top_models_by_pathway.tsv", top_rows, top_fields)
    write_json(output_root / "stats" / "top_models_by_pathway.json", top_rows)


def write_plot(output_root: Path, rows: list[dict[str, Any]]) -> Path | None:
    ok_rows = successful_rows(rows)
    if not ok_rows:
        return None
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None

    values_by_pathway = []
    labels = []
    for pathway in PATHWAYS:
        values = [
            float(row["reaction_retention_percent"])
            for row in ok_rows
            if row.get("pathway") == pathway.slug
            and row.get("reaction_retention_percent") != ""
        ]
        if values:
            values_by_pathway.append(values)
            labels.append(pathway.slug)

    if not values_by_pathway:
        return None

    figure_dir = output_root / "stats" / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    plot_path = figure_dir / "pathway_reaction_retention_boxplot.png"

    fig, ax = plt.subplots(figsize=(8.0, 4.8), dpi=160)
    ax.boxplot(values_by_pathway, labels=labels, showfliers=False)
    for index, values in enumerate(values_by_pathway, start=1):
        xs = [
            index + (((item_index % 9) - 4) * 0.012)
            for item_index, _value in enumerate(values)
        ]
        ax.scatter(xs, values, s=11, alpha=0.45)
    ax.set_ylabel("Matched KEGG reactions, %")
    ax.set_xlabel("KEGG pathway")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(plot_path)
    plt.close(fig)
    return plot_path


def write_readme(
    output_root: Path,
    *,
    selected_count: int,
    excluded_count: int,
    rows: list[dict[str, Any]],
    plot_path: Path | None,
) -> None:
    ok_count = len(successful_rows(rows))
    failed_count = len(rows) - ok_count
    lines = [
        "# BiGG prokaryote BioEMMA batch",
        "",
        f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S %z')}",
        "",
        "## Inputs",
        "",
        f"- BiGG model API: `{BIGG_API_MODELS_URL}`",
        "- Model SBML files: `http://bigg.ucsd.edu/static/models/<model_id>.xml`",
        f"- Selected prokaryotic models: {selected_count}",
        f"- Excluded eukaryotic models: {excluded_count}",
        "",
        "Pathways:",
        "",
    ]
    lines.extend(
        f"- `{pathway.slug}` / `{pathway.rn_id}`: {pathway.label}"
        for pathway in PATHWAYS
    )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `models/`: downloaded BiGG SBML files.",
            "- `kegg_kgml/`: cached KEGG KGML files for the requested pathways.",
            "  `*.drawable.kgml` files omit KEGG reaction entries with no x/y",
            "  coordinates because BioEMMA cannot place them on an Escher map.",
            "- `maps/<pathway>/<model_id>/`: BioEMMA Escher JSON and HTML maps.",
            "- `stats/map_stats.tsv`: one row per model-pathway map.",
            "- `stats/pathway_stats.tsv`: aggregate statistics by pathway.",
            "- `stats/model_stats.tsv`: aggregate statistics by model.",
            "- `stats/top_models_by_pathway.tsv`: top matched models per pathway.",
            "",
            "## Run Summary",
            "",
            f"- Model-pathway maps successful: {ok_count}",
            f"- Model-pathway maps failed: {failed_count}",
        ]
    )
    if plot_path is not None:
        lines.append(f"- Quick plot: `{rel(plot_path)}`")
    lines.extend(
        [
            "",
            "Classification note: BiGG's model-list endpoint does not include a domain",
            "field, so this batch keeps all models except organism strings matching",
            "the known eukaryotic taxa currently present in the BiGG list.",
            "",
        ]
    )
    (output_root / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download prokaryotic BiGG models and build BioEMMA maps for "
            "glycolysis, TCA, pentose phosphate, and methane/C1 metabolism."
        )
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=f"Output folder. Default: {DEFAULT_OUTPUT_ROOT}",
    )
    parser.add_argument(
        "--pathway",
        action="append",
        help=(
            "Pathway to run. Can be repeated. Defaults to map00010, map00020, "
            "map00030, and map00680."
        ),
    )
    parser.add_argument(
        "--model",
        action="append",
        help="Specific BiGG model ID to run. Can be repeated.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit selected models, useful for a smoke test.",
    )
    parser.add_argument(
        "--force-inventory",
        action="store_true",
        help="Refresh the BiGG model inventory even if cached.",
    )
    parser.add_argument(
        "--force-downloads",
        action="store_true",
        help="Redownload SBML and KGML files even if cached.",
    )
    parser.add_argument(
        "--force-maps",
        action="store_true",
        help="Rebuild maps even if outputs already exist.",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Download inventory, KGML, and SBML files without building maps.",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Write Escher JSON maps only. By default HTML maps are saved too.",
    )
    parser.add_argument(
        "--include-eukaryotes",
        action="store_true",
        help="Keep eukaryotic BiGG models too. Off by default.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    configure_cobra_cache(output_root / ".cobra_cache")

    pathways = [normalize_pathway(value) for value in args.pathway] if args.pathway else list(PATHWAYS)
    model_filter = set(args.model) if args.model else None
    session = make_session()

    models = load_bigg_inventory(session, output_root, force=args.force_inventory)
    rows = inventory_rows(models)
    write_tsv(output_root / "inventory" / "bigg_model_inventory.tsv", rows, INVENTORY_FIELDS)
    write_json(output_root / "inventory" / "bigg_model_inventory.json", rows)

    excluded_rows = [
        row for row in rows if row["domain_classification"] != "prokaryote_selected"
    ]
    prokaryote_rows = [
        row for row in rows if row["domain_classification"] == "prokaryote_selected"
    ]
    write_tsv(
        output_root / "inventory" / "prokaryotic_models.tsv",
        prokaryote_rows,
        INVENTORY_FIELDS,
    )
    write_tsv(
        output_root / "inventory" / "excluded_eukaryotic_models.tsv",
        excluded_rows,
        INVENTORY_FIELDS,
    )

    selected_models = select_models(
        models,
        model_filter=model_filter,
        limit=args.limit,
        include_eukaryotes=args.include_eukaryotes,
    )
    log(
        f"Selected {len(selected_models)} models "
        f"({len(prokaryote_rows)} prokaryotic in inventory, {len(excluded_rows)} excluded)"
    )

    kgml_original_paths = {
        pathway.rn_id: ensure_kgml(
            session,
            pathway,
            output_root / "kegg_kgml",
            force=args.force_downloads,
        )
        for pathway in pathways
    }
    kgml_paths: dict[str, Path] = {}
    kgml_sanitization: dict[str, dict[str, Any]] = {}
    for pathway in pathways:
        drawable_path, metadata = sanitize_kgml_for_bioemma(
            kgml_original_paths[pathway.rn_id],
            force=args.force_downloads,
        )
        kgml_paths[pathway.rn_id] = drawable_path
        kgml_sanitization[pathway.rn_id] = metadata
        if metadata["removed_reaction_entry_count"]:
            log(
                f"{pathway.slug}: omitted "
                f"{metadata['removed_reaction_entry_count']} KEGG reaction entries "
                "without drawable coordinates"
            )

    downloaded_models: dict[str, Path] = {}
    for index, model_meta in enumerate(selected_models, start=1):
        model_id = str(model_meta["bigg_id"])
        try:
            model_path, download_status = ensure_model_xml(
                session,
                model_meta,
                output_root / "models",
                force=args.force_downloads,
            )
            downloaded_models[model_id] = model_path
            log(f"Model {index}/{len(selected_models)} ready: {model_id} ({download_status})")
        except Exception as error:
            log(f"Download failed for {model_id}: {error}")

    if args.download_only:
        log("Download-only mode complete")
        write_readme(
            output_root,
            selected_count=len(selected_models),
            excluded_count=len(excluded_rows),
            rows=[],
            plot_path=None,
        )
        return 0

    import cobra

    metabolite_mapper = MetaNetXMapper(resource_path("metabolite_mapping.tsv"), "first")
    map_rows: list[dict[str, Any]] = []
    total_maps = len(selected_models) * len(pathways)
    completed_maps = 0

    for model_index, model_meta in enumerate(selected_models, start=1):
        model_id = str(model_meta["bigg_id"])
        model_xml = downloaded_models.get(model_id)
        if model_xml is None:
            for pathway in pathways:
                map_rows.append(
                    stats_row(
                        status="failed",
                        model_meta=model_meta,
                        model_xml=None,
                        pathway=pathway,
                        error="model download failed",
                    )
                )
            write_map_stats(output_root, map_rows)
            continue

        log(f"Loading {model_id} ({model_index}/{len(selected_models)})")
        try:
            cobra_model = cobra.io.read_sbml_model(str(model_xml))
        except Exception as error:
            error_text = f"model load failed: {error}"
            log(error_text)
            write_json(
                output_root / "maps" / "_errors" / f"{model_id}_load_error.json",
                {
                    "bigg_id": model_id,
                    "model_xml": str(model_xml),
                    "error": error_text,
                    "traceback": traceback.format_exc(),
                },
            )
            for pathway in pathways:
                map_rows.append(
                    stats_row(
                        status="failed",
                        model_meta=model_meta,
                        model_xml=model_xml,
                        pathway=pathway,
                        error=error_text,
                    )
                )
            write_map_stats(output_root, map_rows)
            continue

        for pathway in pathways:
            completed_maps += 1
            log(
                f"Building {completed_maps}/{total_maps}: "
                f"{model_id} on {pathway.slug}"
            )
            try:
                row = build_one_map(
                    cobra_model=cobra_model,
                    model_meta=model_meta,
                    model_xml=model_xml,
                    pathway=pathway,
                    kgml_path=kgml_paths[pathway.rn_id],
                    kgml_sanitization=kgml_sanitization[pathway.rn_id],
                    output_root=output_root,
                    metabolite_mapper=metabolite_mapper,
                    force_maps=args.force_maps,
                    save_html_files=not args.no_html,
                )
            except Exception as error:
                error_text = str(error)
                log(f"Map failed for {model_id} {pathway.slug}: {error_text}")
                error_dir = output_root / "maps" / pathway.slug / model_id
                write_json(
                    error_dir / "error.json",
                    {
                        "bigg_id": model_id,
                        "organism": model_meta.get("organism", ""),
                        "pathway": pathway.slug,
                        "pathway_rn": pathway.rn_id,
                        "model_xml": str(model_xml),
                        "kgml": str(kgml_paths[pathway.rn_id]),
                        "kgml_sanitization": kgml_sanitization[pathway.rn_id],
                        "error": error_text,
                        "traceback": traceback.format_exc(),
                    },
                )
                row = stats_row(
                    status="failed",
                    model_meta=model_meta,
                    model_xml=model_xml,
                    pathway=pathway,
                    error=error_text,
                )
            map_rows.append(row)
            write_map_stats(output_root, map_rows)

    write_aggregates(output_root, map_rows)
    plot_path = write_plot(output_root, map_rows)
    write_readme(
        output_root,
        selected_count=len(selected_models),
        excluded_count=len(excluded_rows),
        rows=map_rows,
        plot_path=plot_path,
    )

    log(f"Done. Outputs: {output_root}")
    log(f"Map stats: {output_root / 'stats' / 'map_stats.tsv'}")
    if plot_path is not None:
        log(f"Plot: {plot_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
