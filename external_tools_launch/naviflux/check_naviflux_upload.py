from __future__ import annotations

import argparse
from pathlib import Path

import requests


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = (
    REPO_ROOT
    / "figures_scripts"
    / "fig4_naviflux"
    / "outputs"
    / "naviflux"
    / "e_coli_core_map00010_reactions.xml"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload the Figure 4 model to NAViFluX.")
    parser.add_argument("--api", default="http://127.0.0.1:5000")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.model.open("rb") as file:
        response = requests.post(
            f"{args.api}/api/v1/cobra-model",
            files={"file": (args.model.name, file, "application/xml")},
            timeout=60,
        )
    response.raise_for_status()
    print(response.text[:1000])


if __name__ == "__main__":
    main()
