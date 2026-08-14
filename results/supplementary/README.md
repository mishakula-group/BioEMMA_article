# Supplementary materials crosswalk

This folder keeps the full `rn00010` BioEMMA maps and serves as the index for
the submitted Supplementary Figures S1-S14. The submitted package contains
rendered image/report exports; this repository keeps the corresponding source,
interactive, or retained publication files.

Current submitted export names:

| Supplement | Submitted export file(s) |
|---|---|
| S1 | `S1. map00010_KEGG.png` |
| S2 | `S2. map00010_escher_KEGG.png` |
| S3 | `S3. map00010_model-specific_map.png` |
| S4 | `S4. map00010_model-specific_map_with_fluxes.png` |
| S5 | `S5. SAMMI.jpg` |
| S6 | `S6. Fluxer_png.png`, `S6. Fluxer_svg.svg` |
| S7 | `S7. CAVE_D-glucose_pathway_jpg.jpg`, `S7. CAVE_D-glucose_pathway_svg.svg` |
| S8 | `S8. Grohar.png` |
| S9 | `S9. MetExplore V2.png` |
| S10 | `S10.memote_diff_report.html` |
| S11 | `S11. map00020_KEGG.png` |
| S12 | `S12. map00020_gapseq.png` |
| S13 | `S13. map00020_modelseed.png` |
| S14 | `S14. map00020_reconstructor.png` |

## S1-S4: glycolysis/gluconeogenesis, `map00010` / `rn00010`

- S1, KEGG reference map for glycolysis/gluconeogenesis:
  `rn00010/kegg_source_reconstruction.json`.
- S2, Escher visualization of the KEGG-derived map:
  `rn00010/kegg_escher_map.html` and `rn00010/kegg_escher_map.json`.
- S3, BioEMMA model-specific `e_coli_core` map:
  `rn00010/escher_map.html` and `rn00010/escher_map.json`.
- S4, BioEMMA model-specific map with flux overlay:
  `rn00010/escher_map_with_fluxes.html` and `rn00010/fluxes.json`.

## S5-S9: external visualization tools

- S5, SAMMI visualization: `../fig5_tool_comparison/sammi_full.html`.
- S6, Fluxer visualization:
  `../fig5_tool_comparison/fluxer_e_coli_core.svg`,
  `../fig5_tool_comparison/fluxer_e_coli_core.png`, and
  `../fig5_tool_comparison/fluxer_e_coli_core.html`.
- S7, CAVE visualization:
  `../fig5_tool_comparison/cave_d_glucose.svg`.
- S8, Grohar visualization:
  `../fig5_tool_comparison/grohar_output.png`.
- S9, MetExplore V2 visualization:
  `../fig5_tool_comparison/metexplore_v2_visualization.png`.

## S10: MEMOTE comparison report

- S10, MEMOTE comparison report between gapseq, ModelSEEDpy, and Reconstructor:
  `../../pipeline_three_reconstructors_outputs/10_memote_reports/SRR13921546_ecoli_M9_vit_aa_memote_diff_report.html`.

## S11-S14: citrate cycle, `map00020`

- S11, KEGG reference/source reconstruction for the citrate cycle:
  `../figure_03/map00020/gapseq/kegg_source_reconstruction.json`
  (the same KEGG source reconstruction is also stored in the ModelSEEDpy and
  Reconstructor map folders).
- S12, BioEMMA `map00020` visualization for gapseq:
  `../figure_03/map00020/gapseq/gapseq_map00020_map.html` and
  `../figure_03/map00020/gapseq/gapseq_map00020_full_with_fluxes.html`.
- S13, BioEMMA `map00020` visualization for ModelSEEDpy:
  `../figure_03/map00020/modelseed/modelseed_map00020_map.html` and
  `../figure_03/map00020/modelseed/modelseed_map00020_full_with_fluxes.html`.
- S14, BioEMMA `map00020` visualization for Reconstructor:
  `../figure_03/map00020/reconstructor/reconstructor_map00020_map.html` and
  `../figure_03/map00020/reconstructor/reconstructor_map00020_full_with_fluxes.html`.

Rendered article/MDPI supplementary images may be exported from these
HTML/SVG/PNG materials. Summary-only scratch files are intentionally not kept.
