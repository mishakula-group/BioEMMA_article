from __future__ import annotations

import csv
import html
import json
import os
import statistics
import argparse
import time
from copy import deepcopy
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build compartment-specific BioEMMA maps for eukaryotic models."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "outputs" / "compartment_maps",
        help="Working output root. Final curated outputs are stored in results/compartments.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(os.environ.get("BIOEMMA_COMPARTMENT_SOURCE_ROOT", REPO_ROOT / "data" / "compartment_models")),
        help=(
            "Directory containing the iMM904, iMM1415, Recon3D, and KGML inputs "
            "using the same subfolder layout as the original benchmark run."
        ),
    )
    return parser.parse_args()


ARGS = parse_args()
OUTPUT_ROOT = ARGS.output_root.resolve()
SOURCE_ROOT = ARGS.source_root.resolve()
OUT_DIR = OUTPUT_ROOT / "compartments"
CACHE_DIR = OUTPUT_ROOT / "cobra_cache"
KGML_DIR = SOURCE_ROOT / "recon3d_probe" / "kgml"

os.environ.setdefault("BIOEMMA_COBRA_CACHE_DIR", str(CACHE_DIR))
os.environ.setdefault("COBRA_CACHE_DIR", str(CACHE_DIR))

PADDING = 150.0
TITLE_HEIGHT = 110.0
GAP_X = 210.0

MODEL_SPECS = [
    {
        "key": "yeast_iMM904",
        "organism": "Saccharomyces cerevisiae",
        "model_id": "iMM904",
        "path": SOURCE_ROOT / "compartment_probe" / "iMM904.xml",
        "objective": None,
        "pathways": [
            ("rn00010", "Glycolysis / Gluconeogenesis", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00020", "Citrate cycle (TCA cycle)", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00620", "Pyruvate metabolism", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00630", "Glyoxylate and dicarboxylate metabolism", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00071", "Fatty acid degradation", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00290", "Valine, leucine and isoleucine biosynthesis", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
        ],
    },
    {
        "key": "mouse_iMM1415",
        "organism": "Mus musculus",
        "model_id": "iMM1415",
        "path": SOURCE_ROOT / "organism_benchmark" / "models" / "iMM1415.xml",
        "objective": "BIOMASS_mm_1_no_glygln",
        "pathways": [
            ("rn00020", "Citrate cycle (TCA cycle)", [("c", "cytosol"), ("m", "mitochondria")]),
            ("rn00620", "Pyruvate metabolism", [("c", "cytosol"), ("m", "mitochondria")]),
            ("rn00630", "Glyoxylate and dicarboxylate metabolism", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00280", "Valine, leucine and isoleucine degradation", [("c", "cytosol"), ("m", "mitochondria")]),
            ("rn00100", "Steroid biosynthesis", [("c", "cytosol"), ("r", "endoplasmic reticulum"), ("m", "mitochondria")]),
        ],
    },
    {
        "key": "human_Recon3D",
        "organism": "Homo sapiens",
        "model_id": "Recon3D",
        "path": SOURCE_ROOT / "recon3d_probe" / "Recon3D.xml",
        "objective": None,
        "pathways": [
            ("rn00020", "Citrate cycle (TCA cycle)", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00620", "Pyruvate metabolism", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00071", "Fatty acid degradation", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome"), ("r", "endoplasmic reticulum")]),
            ("rn00100", "Steroid biosynthesis", [("c", "cytosol"), ("r", "endoplasmic reticulum"), ("m", "mitochondria")]),
            ("rn00240", "Pyrimidine metabolism", [("c", "cytosol"), ("m", "mitochondria"), ("n", "nucleus")]),
            ("rn00280", "Valine, leucine and isoleucine degradation", [("c", "cytosol"), ("m", "mitochondria"), ("x", "peroxisome/glyoxysome")]),
            ("rn00480", "Glutathione metabolism", [("c", "cytosol"), ("m", "mitochondria"), ("e", "extracellular space")]),
            ("rn00564", "Glycerophospholipid metabolism", [("c", "cytosol"), ("r", "endoplasmic reticulum"), ("m", "mitochondria"), ("e", "extracellular space")]),
            ("rn00670", "One carbon pool by folate", [("c", "cytosol"), ("m", "mitochondria")]),
        ],
    },
]


def configure_cache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    import appdirs

    original = appdirs.user_cache_dir

    def user_cache_dir(appname=None, appauthor=None, *args, **kwargs):
        if appname == "cobrapy" and appauthor == "opencobra":
            return str(CACHE_DIR)
        return original(appname, appauthor, *args, **kwargs)

    appdirs.user_cache_dir = user_cache_dir


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_flux_html(path: Path, map_json_path: Path, reaction_data: dict[str, float]) -> None:
    import escher

    path.parent.mkdir(parents=True, exist_ok=True)
    escher.Builder(map_json=str(map_json_path), reaction_data=reaction_data).save_html(str(path))


def coord_pairs(obj: dict[str, Any]) -> list[tuple[str, str]]:
    return [(x, y) for x, y in (("x", "y"), ("label_x", "label_y")) if x in obj and y in obj]


def shift_obj(obj: dict[str, Any], dx: float, dy: float) -> None:
    for x, y in coord_pairs(obj):
        obj[x] = float(obj[x]) + dx
        obj[y] = float(obj[y]) + dy


def shift_map(escher_map: list[dict[str, Any]], dx: float, dy: float) -> list[dict[str, Any]]:
    shifted = deepcopy(escher_map)
    model = shifted[1]
    for node in model.get("nodes", {}).values():
        shift_obj(node, dx, dy)
    for reaction in model.get("reactions", {}).values():
        shift_obj(reaction, dx, dy)
        for segment in reaction.get("segments", {}).values():
            for bend_key in ("b1", "b2"):
                bend = segment.get(bend_key)
                if isinstance(bend, dict):
                    shift_obj(bend, dx, dy)
    for label in model.get("text_labels", {}).values():
        shift_obj(label, dx, dy)
    model.pop("canvas", None)
    return shifted


def all_points(escher_map: list[dict[str, Any]]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    model = escher_map[1]
    for node in model.get("nodes", {}).values():
        for x, y in coord_pairs(node):
            points.append((float(node[x]), float(node[y])))
    for reaction in model.get("reactions", {}).values():
        for x, y in coord_pairs(reaction):
            points.append((float(reaction[x]), float(reaction[y])))
        for segment in reaction.get("segments", {}).values():
            for bend_key in ("b1", "b2"):
                bend = segment.get(bend_key)
                if isinstance(bend, dict):
                    for x, y in coord_pairs(bend):
                        points.append((float(bend[x]), float(bend[y])))
    return points or [(0.0, 0.0), (1000.0, 1000.0)]


def bounds(escher_map: list[dict[str, Any]]) -> dict[str, float]:
    points = all_points(escher_map)
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}


def reaction_positions(escher_map: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    out = {}
    for reaction in escher_map[1].get("reactions", {}).values():
        key = str(reaction.get("name") or reaction.get("bigg_id") or "")
        if key.startswith("R") and len(key) == 6:
            out[key] = (float(reaction.get("label_x", 0.0)), float(reaction.get("label_y", 0.0)))
    return out


def median_translation(reference: dict[str, tuple[float, float]], current: dict[str, tuple[float, float]]) -> tuple[float, float, int]:
    shared = sorted(set(reference) & set(current))
    if not shared:
        return 0.0, 0.0, 0
    return (
        float(statistics.median(reference[key][0] - current[key][0] for key in shared)),
        float(statistics.median(reference[key][1] - current[key][1] for key in shared)),
        len(shared),
    )


def clone_panel(escher_map: list[dict[str, Any]], base_id: int, dx: float, dy: float) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    model = escher_map[1]
    node_map = {str(node_id): str(base_id + i) for i, node_id in enumerate(sorted(model.get("nodes", {})), 1)}
    nodes: dict[str, Any] = {}
    reactions: dict[str, Any] = {}
    labels: dict[str, Any] = {}

    for node_id, node in model.get("nodes", {}).items():
        copied = deepcopy(node)
        shift_obj(copied, dx, dy)
        nodes[node_map[str(node_id)]] = copied

    for r_i, (_reaction_id, reaction) in enumerate(sorted(model.get("reactions", {}).items()), 1):
        copied = deepcopy(reaction)
        shift_obj(copied, dx, dy)
        segments = {}
        for s_i, (_segment_id, segment) in enumerate(sorted(copied.get("segments", {}).items()), 1):
            seg = deepcopy(segment)
            from_node_id = node_map.get(str(seg.get("from_node_id")))
            to_node_id = node_map.get(str(seg.get("to_node_id")))
            if from_node_id is None or to_node_id is None:
                continue
            seg["from_node_id"] = from_node_id
            seg["to_node_id"] = to_node_id
            for bend_key in ("b1", "b2"):
                bend = seg.get(bend_key)
                if isinstance(bend, dict):
                    shift_obj(bend, dx, dy)
            segments[str(base_id + 600000 + r_i * 1000 + s_i)] = seg
        copied["segments"] = segments
        reactions[str(base_id + 300000 + r_i)] = copied

    for l_i, (_label_id, label) in enumerate(sorted(model.get("text_labels", {}).items()), 1):
        copied = deepcopy(label)
        shift_obj(copied, dx, dy)
        labels[str(base_id + 900000 + l_i)] = copied

    return nodes, reactions, labels


def remove_invalid_segments(escher_map: list[dict[str, Any]]) -> None:
    nodes = escher_map[1].get("nodes", {})
    for reaction in escher_map[1].get("reactions", {}).values():
        reaction["segments"] = {
            str(segment_id): segment
            for segment_id, segment in reaction.get("segments", {}).items()
            if str(segment.get("from_node_id")) in nodes and str(segment.get("to_node_id")) in nodes
        }


def build_aligned_map(spec: dict[str, Any], pathway: str, title: str, compartments: list[tuple[str, str]], maps: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reference = max(maps, key=lambda compartment: len(maps[compartment][1].get("reactions", {})))
    ref_positions = reaction_positions(maps[reference])
    translations = {reference: {"dx": 0.0, "dy": 0.0, "anchors": len(ref_positions)}}
    for compartment, escher_map in maps.items():
        if compartment == reference:
            continue
        dx, dy, anchors = median_translation(ref_positions, reaction_positions(escher_map))
        translations[compartment] = {"dx": dx, "dy": dy, "anchors": anchors}

    shifted = {comp: shift_map(m, values["dx"], values["dy"]) for comp, (m, values) in ((c, (maps[c], translations[c])) for c in maps)}
    boxes = {comp: bounds(m) for comp, m in shifted.items()}
    global_box = {
        "min_x": min(box["min_x"] for box in boxes.values()),
        "max_x": max(box["max_x"] for box in boxes.values()),
        "min_y": min(box["min_y"] for box in boxes.values()),
        "max_y": max(box["max_y"] for box in boxes.values()),
    }
    cell_w = global_box["max_x"] - global_box["min_x"]
    cell_h = global_box["max_y"] - global_box["min_y"]

    nodes: dict[str, Any] = {}
    reactions: dict[str, Any] = {}
    labels: dict[str, Any] = {"9900001": {"x": PADDING, "y": 48.0, "text": f"{spec['model_id']} {pathway}: {title}"}}
    used = [(comp, label) for comp, label in compartments if comp in shifted]
    for i, (comp, label) in enumerate(used):
        origin_x = PADDING + i * (cell_w + GAP_X)
        origin_y = PADDING + TITLE_HEIGHT
        panel_nodes, panel_reactions, panel_labels = clone_panel(
            shifted[comp],
            (i + 1) * 1000000,
            origin_x - global_box["min_x"],
            origin_y - global_box["min_y"],
        )
        nodes.update(panel_nodes)
        reactions.update(panel_reactions)
        labels.update(panel_labels)
        labels[str(9900002 + i)] = {"x": origin_x, "y": origin_y - 42.0, "text": f"{comp}: {label}"}

    aligned = [
        {
            "map_name": f"{spec['model_id']} {pathway} compartment comparison",
            "map_id": f"{spec['model_id']}_{pathway}_compartments_041",
            "map_description": "BioEMMA 0.4.1 compartment-filtered maps aligned to one KEGG coordinate frame.",
            "homepage": "https://escher.github.io",
            "schema": "https://escher.github.io/escher/jsonschema/1-0-0#",
        },
        {
            "reactions": reactions,
            "nodes": nodes,
            "text_labels": labels,
            "canvas": {
                "x": 0.0,
                "y": 0.0,
                "width": PADDING * 2 + len(used) * cell_w + max(0, len(used) - 1) * GAP_X,
                "height": PADDING * 2 + TITLE_HEIGHT + cell_h,
            },
        },
    ]
    remove_invalid_segments(aligned)
    max_y_delta = 0.0
    for comp, escher_map in maps.items():
        for key, pos in reaction_positions(escher_map).items():
            if key in ref_positions:
                max_y_delta = max(max_y_delta, abs((pos[1] + translations[comp]["dy"]) - ref_positions[key][1]))
    return aligned, {
        "reference_compartment": reference,
        "translations": translations,
        "max_shared_y_delta_after_alignment": max_y_delta,
        "reaction_counts": {comp: len(escher_map[1].get("reactions", {})) for comp, escher_map in maps.items()},
        "canvas": aligned[1]["canvas"],
    }


def flux_summary(escher_map: list[dict[str, Any]], fluxes: dict[str, float], compartments: list[tuple[str, str]]) -> dict[str, Any]:
    by_comp = {comp: {"mapped": 0, "with_flux": 0, "nonzero_flux": 0} for comp, _ in compartments}
    rows = []
    for reaction in escher_map[1].get("reactions", {}).values():
        compartment = None
        for metabolite in reaction.get("metabolites", []):
            if metabolite.get("compartment"):
                compartment = metabolite.get("compartment")
                break
        bigg_id = str(reaction.get("bigg_id") or "")
        value = fluxes.get(bigg_id)
        if compartment in by_comp:
            by_comp[compartment]["mapped"] += 1
            if value is not None:
                by_comp[compartment]["with_flux"] += 1
                if abs(float(value)) > 1e-9:
                    by_comp[compartment]["nonzero_flux"] += 1
        rows.append({"compartment": compartment, "kegg": reaction.get("name"), "bigg_id": bigg_id, "flux": value})
    return {"by_compartment": by_comp, "rows": sorted(rows, key=lambda row: (str(row["compartment"]), str(row["kegg"]), str(row["bigg_id"])))}


def write_flux_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["compartment", "kegg", "bigg_id", "flux"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def stat(values: list[float]) -> dict[str, float]:
    if not values:
        return {"n": 0, "mean_sec": 0.0, "median_sec": 0.0, "min_sec": 0.0, "max_sec": 0.0, "total_sec": 0.0}
    return {
        "n": len(values),
        "mean_sec": statistics.mean(values),
        "median_sec": statistics.median(values),
        "min_sec": min(values),
        "max_sec": max(values),
        "total_sec": sum(values),
    }


def html_index(all_summaries: list[dict[str, Any]], timing_summary: dict[str, Any]) -> str:
    rows = []
    for item in all_summaries:
        counts = ", ".join(f"{k}={v}" for k, v in item["reaction_counts"].items())
        nonzero = ", ".join(f"{k}={v['nonzero_flux']}" for k, v in item["flux_summary"]["by_compartment"].items())
        rel = Path(item["html"]).relative_to(OUT_DIR)
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['organism'])}</td><td>{html.escape(item['model_id'])}</td>"
            f"<td>{html.escape(item['pathway'])}</td><td>{html.escape(item['title'])}</td>"
            f"<td>{html.escape(counts)}</td><td>{html.escape(nonzero)}</td>"
            f"<td>{item['alignment']['max_shared_y_delta_after_alignment']:.3g}</td>"
            f"<td><a href=\"{html.escape(rel.as_posix())}\">HTML</a></td>"
            "</tr>"
        )
    timing_rows = []
    for key, value in timing_summary["summary_by_model"].items():
        timing_rows.append(
            "<tr>"
            f"<td>{html.escape(key)}</td><td>{value['n']}</td>"
            f"<td>{value['mean_sec']:.3f}</td><td>{value['median_sec']:.3f}</td>"
            f"<td>{value['min_sec']:.3f}</td><td>{value['max_sec']:.3f}</td>"
            f"<td>{value['total_sec']:.1f}</td>"
            "</tr>"
        )
    return (
        "<!doctype html><meta charset=\"utf-8\"><title>BioEMMA 0.4.1 compartment maps</title>"
        "<style>body{font-family:Arial,sans-serif;margin:32px;line-height:1.4}table{border-collapse:collapse;margin:18px 0 28px}"
        "td,th{border:1px solid #ccc;padding:7px 9px;vertical-align:top}th{background:#f4f4f4;text-align:left}</style>"
        "<h1>BioEMMA 0.4.1 compartment maps</h1>"
        "<h2>Maps</h2><table><thead><tr><th>Organism</th><th>Model</th><th>Pathway</th><th>Title</th><th>Reactions</th><th>Nonzero flux</th><th>Max shared y delta</th><th>Map</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table><h2>Timing</h2><table><thead><tr><th>Model</th><th>N</th><th>Mean s</th><th>Median s</th><th>Min s</th><th>Max s</th><th>Total s</th></tr></thead><tbody>"
        + "".join(timing_rows)
        + "</tbody></table>"
    )


def main() -> None:
    configure_cache()
    import importlib.metadata
    from cobra.io import read_sbml_model
    from bioemma.workflow import build_escher_map

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_summaries: list[dict[str, Any]] = []
    timing_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    start_all = time.perf_counter()

    for spec in MODEL_SPECS:
        print(f"loading {spec['key']}")
        t0 = time.perf_counter()
        model = read_sbml_model(str(spec["path"]))
        load_sec = time.perf_counter() - t0
        if spec["objective"]:
            model.objective = spec["objective"]
        t0 = time.perf_counter()
        solution = model.optimize()
        fba_sec = time.perf_counter() - t0
        fluxes = {str(key): float(value) for key, value in solution.fluxes.to_dict().items()}
        model_rows.append({
            "key": spec["key"],
            "organism": spec["organism"],
            "model_id": spec["model_id"],
            "path": str(spec["path"]),
            "objective": spec["objective"],
            "reactions": len(model.reactions),
            "metabolites": len(model.metabolites),
            "genes": len(model.genes),
            "load_sec": load_sec,
            "fba_sec": fba_sec,
            "fba_status": solution.status,
            "objective_value": None if solution.objective_value is None else float(solution.objective_value),
        })

        model_out = OUT_DIR / spec["key"]
        write_json(model_out / "fba_fluxes.json", {"status": solution.status, "objective_value": None if solution.objective_value is None else float(solution.objective_value), "reaction_data": fluxes})

        for pathway, title, compartments in spec["pathways"]:
            maps: dict[str, list[dict[str, Any]]] = {}
            compartment_summaries: dict[str, Any] = {}
            for compartment, label in compartments:
                t0 = time.perf_counter()
                escher_map, reconstruction = build_escher_map(
                    model,
                    kgml=KGML_DIR / f"{pathway}.xml",
                    database="BIGG",
                    use_model_metabolite_ids=True,
                    metabolite_id_compartments=True,
                    compartment=compartment,
                )
                build_sec = time.perf_counter() - t0
                maps[compartment] = escher_map
                comp_dir = model_out / pathway / compartment
                write_json(comp_dir / "escher_map.json", escher_map)
                write_json(comp_dir / "kegg_source_reconstruction.json", reconstruction)
                segments = sum(len(reaction.get("segments", {})) for reaction in escher_map[1].get("reactions", {}).values())
                timing_rows.append({
                    "organism": spec["organism"],
                    "model_id": spec["model_id"],
                    "pathway": pathway,
                    "pathway_title": title,
                    "compartment": compartment,
                    "build_sec": build_sec,
                    "mapped_reactions": len(escher_map[1].get("reactions", {})),
                    "nodes": len(escher_map[1].get("nodes", {})),
                    "segments": segments,
                })
                compartment_summaries[compartment] = {
                    "label": label,
                    "reaction_count": len(escher_map[1].get("reactions", {})),
                    "nodes": len(escher_map[1].get("nodes", {})),
                    "segments": segments,
                    "build_sec": build_sec,
                }
                print(f"  {spec['model_id']} {pathway} {compartment}: {build_sec:.3f}s rxns={compartment_summaries[compartment]['reaction_count']}")

            aligned, alignment = build_aligned_map(spec, pathway, title, compartments, maps)
            flux_info = flux_summary(aligned, fluxes, compartments)
            map_json = model_out / pathway / f"{spec['model_id']}_{pathway}_compartments.json"
            html_path = model_out / pathway / f"{spec['model_id']}_{pathway}_compartments.html"
            flux_tsv = model_out / pathway / f"{spec['model_id']}_{pathway}_flux.tsv"
            summary_json = model_out / pathway / "summary.json"
            write_json(map_json, aligned)
            write_flux_tsv(flux_tsv, flux_info["rows"])
            save_flux_html(html_path, map_json, fluxes)
            summary = {
                "organism": spec["organism"],
                "model_id": spec["model_id"],
                "pathway": pathway,
                "title": title,
                "bioemma_version": importlib.metadata.version("bioemma"),
                "kgml": str(KGML_DIR / f"{pathway}.xml"),
                "compartments": compartments,
                "reaction_counts": alignment["reaction_counts"],
                "compartment_summaries": compartment_summaries,
                "alignment": alignment,
                "flux_summary": flux_info,
                "html": str(html_path),
                "map_json": str(map_json),
                "flux_tsv": str(flux_tsv),
                "summary_json": str(summary_json),
            }
            write_json(summary_json, summary)
            all_summaries.append(summary)

    summary_by_model = {
        spec["key"]: stat([row["build_sec"] for row in timing_rows if row["model_id"] == spec["model_id"]])
        for spec in MODEL_SPECS
    }
    summary_by_pathway = {}
    for pathway in sorted({row["pathway"] for row in timing_rows}):
        summary_by_pathway[pathway] = stat([row["build_sec"] for row in timing_rows if row["pathway"] == pathway])
    timing_summary = {
        "bioemma_version": importlib.metadata.version("bioemma"),
        "models": model_rows,
        "summary_by_model": summary_by_model,
        "summary_by_pathway": summary_by_pathway,
        "total_wall_sec": time.perf_counter() - start_all,
        "task_count": len(timing_rows),
        "tasks": timing_rows,
    }
    write_json(OUT_DIR / "index.json", all_summaries)
    write_json(OUT_DIR / "timing.json", timing_summary)
    with (OUT_DIR / "timing.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["organism", "model_id", "pathway", "pathway_title", "compartment", "build_sec", "mapped_reactions", "nodes", "segments"])
        writer.writeheader()
        writer.writerows(timing_rows)
    (OUT_DIR / "index.html").write_text(html_index(all_summaries, timing_summary), encoding="utf-8")
    print(OUT_DIR / "index.html")


if __name__ == "__main__":
    main()
