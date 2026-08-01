# Publication results

This directory contains the curated publication-ready outputs collected for the
BioEMMA article repository. Generated working directories named `outputs/` are
ignored by git; files kept here are the visible article bundle.

The source scripts and reproducible inputs remain in `figures_scripts/`,
`tables_scripts/`, `scripts/`, `data/`, `wdls/`, and `external_tools_launch/`.

## Contents

- `fig3_map00010/` - cropped KEGG and BioEMMA `map00010` panels as Escher
  HTML/JSON, including the flux-overlay panel. These materials support Figure 3
  and part of Figure 4.
- `fig4_naviflux/` - NAViFLuX reference images as PNG files for Figure 4.
- `figure_03/map00020/` - Figure 6 and Supplementary S11-S14 materials: latest
  `map00020` citrate-cycle maps, selected reaction fragments, full-map flux
  overlays, and source model copies. This path is kept because it is cited
  directly in the article.
- `table2_reaction_retention/` - generated Table 2 TSV, rendered Markdown
  table, detailed reaction lists, and KEGG-to-SEED/BiGG mapping split.
- `table_02_kegg_database_mapping/` - all-pathway KEGG-to-SEED/BiGG mapping
  counts for the 153 reaction-containing KEGG maps in
  `data/kegg_pathways.tsv`; this path is kept because it is cited directly in
  the article.
- `supplementary/` - Supplementary S1-S14 crosswalk and full `rn00010` map
  materials for S1-S4.
- `fig5_tool_comparison/` - Figure 5 and Supplementary S5-S9 comparison
  artifacts for SAMMI, Fluxer, CAVE, MetExplore V2, NetworkX/Grohar baselines,
  and the Fluxer input model.

## Provenance

- The KEGG/BioEMMA map panels, NAViFLuX reference images, reaction-retention
  table, all-pathway mapping table, and Supplementary S1-S4 were regenerated
  with the repository scripts.
- Figure 6 and Supplementary S11-S14 were prepared from the final gapseq,
  ModelSEEDpy, and Reconstructor models stored in
  `figure_03/map00020/source_models/`.
- The three-reconstructor pipeline run parameters and retained intermediate
  outputs are stored in `../pipeline_three_reconstructors_outputs/`.
