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
- `fallback/` - BioEMMA 0.4.2 BiGG and ModelSEED/SEED EC-fallback validation,
  resource coverage, and article-map no-change evidence. These files are
  retained for provenance.
- `jaccard/` - no-fallback reaction-set reproducibility and pairwise Jaccard
  metrics for E. coli, broader BiGG prokaryotic model sets, and the selected
  eukaryotic models.
- `prokaryote_maps/` - no-fallback full BiGG prokaryote BioEMMA batch used as the source
  for the Jaccard analysis: 352 Escher HTML/JSON maps for 88 prokaryotic models
  across `map00010`, `map00020`, `map00030`, and `map00680`, with batch
  statistics and cached KEGG KGML files.
- `compartments/` - compartment-specific eukaryotic maps and timing summaries
  for `iMM904`, `iMM1415`, and `Recon3D`, plus the no-fallback eukaryotic
  BioEMMA maps used for the eukaryotic Jaccard comparison.

## Provenance

- The KEGG/BioEMMA map panels, NAViFLuX reference images, reaction-retention
  table, all-pathway mapping table, and Supplementary S1-S4 were regenerated
  with the repository scripts.
- Figure 6 and Supplementary S11-S14 were prepared from the final gapseq,
  ModelSEEDpy, and Reconstructor models stored in
  `figure_03/map00020/source_models/`.
- The three-reconstructor pipeline run parameters and retained intermediate
  outputs are stored in `../pipeline_three_reconstructors_outputs/`.
- The Jaccard, prokaryote-map, and compartment-map materials
  support the additional model-diversity evaluation added during revision.
- The fallback materials remain in the repository as validation/provenance
  files.

