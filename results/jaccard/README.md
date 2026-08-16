# No-fallback model reproducibility metrics

This directory contains no-fallback reaction-set reproducibility metrics for
BioEMMA maps generated from BiGG models.

Key files:

- `ecoli_reaction_reproducibility/` - pairwise Jaccard metrics and reaction
  frequencies for 57 Escherichia coli models, excluding `e_coli_core`.
- `all_models_reaction_reproducibility/` - pairwise Jaccard metrics and reaction
  frequencies for 87 selected prokaryotic BiGG models.
- `eukaryotic_model_reproducibility/` - pairwise Jaccard metrics and reaction
  frequencies for `iMM904`, `iMM1415`, and `Recon3D`.
- `source_map_stats.tsv` - source BioEMMA map-generation statistics used by the
  prokaryotic reproducibility analysis.
- `source_batch_README.md` - provenance for the BiGG prokaryote map-generation
  batch.

The source maps can be regenerated with
`scripts/build_bigg_prokaryote_pathway_maps.py` for prokaryotes. The Jaccard and
reaction-frequency summaries can be rebuilt with
`scripts/compute_map_reaction_reproducibility.py`.




