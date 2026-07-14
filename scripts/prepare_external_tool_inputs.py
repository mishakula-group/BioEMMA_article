from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "outputs" / "external_tools"


def load_model(model_path: Path):
    import cobra

    return cobra.io.read_sbml_model(str(model_path))


def solve_model(model):
    solution = model.optimize()
    if solution.status != "optimal":
        raise RuntimeError(f"Model optimization failed with status: {solution.status}")
    return solution


def write_flux_csv(path: Path, solution) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("reactionId", "flux"))
        writer.writeheader()
        for reaction_id, flux in solution.fluxes.items():
            if abs(float(flux)) > 1e-6:
                writer.writerow({"reactionId": reaction_id, "flux": float(flux)})


def write_naviflux_weights(path: Path, solution) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("id", "value"))
        writer.writeheader()
        for reaction_id, flux in solution.fluxes.items():
            if abs(float(flux)) > 1e-6:
                writer.writerow({"id": reaction_id, "value": float(flux)})


def write_cobra_json(path: Path, model) -> None:
    import cobra

    path.parent.mkdir(parents=True, exist_ok=True)
    cobra.io.save_json_model(model, str(path))


def write_sammi_html(output_dir: Path, model, solution) -> None:
    import numpy as np
    import sammi

    output_dir.mkdir(parents=True, exist_ok=True)

    full_options = sammi.options()
    full_options.htmlName = str(output_dir / "sammi_full.html")
    full_options.load = False
    sammi.plot(model, opts=full_options)

    flux_options = sammi.options()
    flux_options.htmlName = str(output_dir / "sammi_flux.html")
    flux_options.load = False
    flux_data = sammi.data(
        group="reactions",
        kind="color",
        data=np.array(solution.fluxes.values).reshape(-1, 1),
        ids=list(solution.fluxes.index),
        conditions=np.array(["FBA fluxes"]),
    )
    sammi.plot(model, datat=[flux_data], opts=flux_options)


def write_networkx_baseline(path: Path, model, solution) -> None:
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    import networkx as nx

    graph = nx.DiGraph()
    for reaction in model.reactions:
        flux = float(solution.fluxes.get(reaction.id, 0.0))
        if abs(flux) < 1e-9:
            continue
        graph.add_node(reaction.id, node_type="reaction", flux=flux)
        for metabolite, coefficient in reaction.metabolites.items():
            graph.add_node(metabolite.id, node_type="metabolite", flux=0.0)
            if coefficient < 0:
                graph.add_edge(metabolite.id, reaction.id, weight=abs(coefficient))
            else:
                graph.add_edge(reaction.id, metabolite.id, weight=abs(coefficient))

    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(18, 14))
    positions = nx.spring_layout(graph, seed=13, k=0.55)
    reaction_nodes = [
        node for node, data in graph.nodes(data=True) if data["node_type"] == "reaction"
    ]
    metabolite_nodes = [
        node for node, data in graph.nodes(data=True) if data["node_type"] == "metabolite"
    ]
    reaction_fluxes = [abs(graph.nodes[node]["flux"]) for node in reaction_nodes]
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=metabolite_nodes,
        node_size=55,
        node_color="#8bb6d6",
        alpha=0.75,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=reaction_nodes,
        node_size=140,
        node_color=reaction_fluxes,
        cmap=plt.cm.viridis,
        alpha=0.9,
    )
    nx.draw_networkx_edges(graph, positions, width=0.6, alpha=0.25, arrows=False)
    nx.draw_networkx_labels(
        graph,
        positions,
        labels={node: node for node in reaction_nodes},
        font_size=6,
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def run_optional(name: str, callback) -> None:
    try:
        callback()
    except ImportError as error:
        print(f"Skipped {name}: missing dependency ({error.name})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare inputs and reproducible outputs for non-BioEMMA tools."
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DATA_DIR / "e_coli_core.xml",
        help="SBML model path.",
    )
    parser.add_argument(
        "--skip-optional",
        action="store_true",
        help="Only write CSV/JSON inputs; skip SAMMI and NetworkX rendering.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = load_model(args.model)
    solution = solve_model(model)

    write_flux_csv(OUTPUT_DIR / "metexplore_fluxes.csv", solution)
    write_naviflux_weights(OUTPUT_DIR / "naviflux_reaction_weights.csv", solution)
    write_naviflux_weights(OUTPUT_DIR / "naviflux_flux_weights.csv", solution)
    write_cobra_json(OUTPUT_DIR / "model_for_fluxer.json", model)

    if not args.skip_optional:
        run_optional(
            "SAMMI",
            lambda: write_sammi_html(OUTPUT_DIR / "sammi", model, solution),
        )
        run_optional(
            "NetworkX baseline",
            lambda: write_networkx_baseline(
                OUTPUT_DIR / "networkx" / "networkx_baseline.png",
                model,
                solution,
            ),
        )

    print(f"Wrote external-tool materials to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
