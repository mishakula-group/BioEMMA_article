# BioEMMA Article Materials

This repository contains the publication materials used for the BioEMMA article:
prepared figures, supplementary files, comparison artifacts, source data, and the
scripts needed to regenerate the tables and maps.

For readers, start with `results/`. The script and workflow folders are included
to show how the publication materials were generated and how the article test
cases can be repeated.

## Article crosswalk

The list below follows the article numbering.

- Figure 1: BioEMMA workflow schematic in the manuscript.
- Figure 2: BioUML pipeline schematic in the manuscript; runnable WDLs are in
  `wdls/`.
- Figure 3 and Supplementary Figures S1-S4: `results/fig3_map00010/` and
  `results/supplementary/rn00010/`.
- Figure 4: NAViFLuX reference images in `results/fig4_naviflux/`, with the
  matching `map00010` BioEMMA/Escher fragments in `results/fig3_map00010/`.
- Figure 5 and Supplementary Table S1:
  `results/fig5_tool_comparison/tool_comparison_matrix.png`,
  `results/fig5_tool_comparison/tool_comparison.html`, and
  `results/fig5_tool_comparison/supplementary_table_s1_tool_descriptions.tsv`.
- Figure 6 and Supplementary Figures S11-S14: `results/figure_03/map00020/`.
  This path is kept because it is cited directly in the article.
- Additional model-diversity materials for Supplementary Table S3:
  `results/jaccard/`, `results/prokaryote_maps/`, `results/compartments/no_fallback_maps/`,
  and `results/compartments/`.
- EC-fallback validation materials retained for provenance:
  `results/fallback/`.
- Table 2: `results/table2_reaction_retention/`.
- Supplementary Table S2 reaction-level summaries:
  `results/table2_reaction_retention/`.
- Pathway-wide KEGG mapping data discussed in the limitations:
  `results/table_02_kegg_database_mapping/`. This path is kept because the
  article cites it directly.
- WDL workflows and the Scenario III article run parameters: `wdls/` and
  `pipeline_three_reconstructors_outputs/00_workflow/`.
- Pipeline outputs for the three-reconstructor test case:
  `pipeline_three_reconstructors_outputs/`.

The full supplementary-material mapping is listed in
`results/supplementary/README.md`.

## Repository layout

- `results/` - publication-ready materials grouped by figure, table, and supplement.
- `data/` - shared source inputs, including the KEGG pathway list used for the all-pathway mapping table.
- `figures_scripts/` - scripts used to build figure-specific BioEMMA, Escher, and NAViFLuX materials.
- `tables_scripts/` - scripts used to build article tables.
- `wdls/` - WDL workflows for local/Cromwell execution of the BioUML pipeline scenarios.
- `pipeline_three_reconstructors_outputs/` - retained outputs from the Scenario III
  run on SRR13921546 using gapseq, ModelSEEDpy, and Reconstructor.
- `external_tools_launch/` - launch notes for external visualization tools.
- `scripts/` - helper scripts for external-tool input preparation,
  comparison-matrix generation, prokaryotic-map reproducibility, fallback
  summaries, and compartment-map generation.

Generated working folders named `outputs/` are intentionally ignored by git. Curated outputs
that should be visible to readers are copied into `results/`.

Rebuild commands are documented only in the README next to the relevant script
or workflow.

