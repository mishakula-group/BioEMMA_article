# map00020 reconstruction-comparison results

This directory contains the publication materials for KEGG `map00020` (citrate
cycle / TCA cycle). The `figure_03` parent folder is kept because the article
cites this path directly.

These files support Figure 6 and Supplementary Figures S11-S14.

## Full maps

Each reconstruction has a full BioEMMA map:

- `gapseq/gapseq_map00020_map.html`
- `modelseed/modelseed_map00020_map.html`
- `reconstructor/reconstructor_map00020_map.html`

## Full maps with flux overlay

The full-map flux overlays keep the BiGG-priority visualization layout and add
model-specific flux distributions:

- `gapseq/gapseq_map00020_full_with_fluxes.html`
- `modelseed/modelseed_map00020_full_with_fluxes.html`
- `reconstructor/reconstructor_map00020_full_with_fluxes.html`

The accompanying `*_full_fluxes.json` files contain the optimized flux values and
reaction matching details used for each overlay.

## Supplementary mapping

- S11: `kegg_source_reconstruction.json` in each model folder records the KEGG
  source reconstruction used for the `map00020` reference geometry.
- S12: `gapseq/`.
- S13: `modelseed/`.
- S14: `reconstructor/`.

## Selected reaction fragments

The `selected_reaction_fragments/` directory contains cropped fragments for the
article panels, including versions with flux overlays.

## Source models

The `source_models/` directory contains the latest reconstructed models used for
the `map00020` outputs in this publication bundle.
