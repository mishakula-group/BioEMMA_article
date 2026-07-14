# Publication results

This directory contains the trimmed publication-ready outputs collected for the BioEMMA article repository.

The source scripts and reproducible inputs remain in `figures/`, `scripts/`, `data/`, and
`external_tools/`. Generated working directories named `outputs/` are intentionally ignored by
git; this `results/` directory is the tracked publication bundle.

## Contents

- `figure_01/fragment/` - cropped KEGG and BioEMMA Figure 1 map panels as Escher HTML/JSON, plus the retained Figure 1 flux-overlay panel.
- `figure_02/naviflux_full_reference/` - Figure 2 NAViFLuX reference images as PNG only; JSON, SVG, model, and table inputs were removed from the publication bundle.
- `figure_03/map00020/` - latest Figure 3 `map00020` citrate-cycle maps and selected reaction fragments from `.temp_models_check/outputs/map00020`; `rn00010` outputs and old-model comparison files were removed.
- `figure_03/map00020/source_models/` - latest reconstructed source models used for the Figure 3 `map00020` run.
- `table_01/` - generated Table 1 TSV, rendered Markdown table, and detailed reaction lists.
- `supplementary/` - supplementary full `rn00010` map materials; see `supplementary/README.md`.
- `external_tool_comparison/` - prepared external-tool comparison artifacts. Flux/flow files and the duplicate CSV table were removed.

Summary files were removed from the publication bundle.

## Provenance

- Figure 1, Figure 2, Table 1, and supplementary outputs were regenerated in `BioEMMA_article` on 2026-07-14 using the repository scripts.
- Figure 3 models and `map00020` outputs were copied from `article_materials_repo/.temp_models_check`, which contains the latest model run.
- Existing repository files outside `results/` were not rewritten for this publication bundle.
