# Prokaryotic model reproducibility metrics

This directory contains reaction-set reproducibility metrics for BioEMMA maps
generated from BiGG prokaryotic models.

Key files:

- `ecoli_reaction_reproducibility/` - pairwise Jaccard metrics and reaction
  frequencies for 57 Escherichia coli models, excluding `e_coli_core`.
- `all_models_reaction_reproducibility/` - pairwise Jaccard metrics and reaction
  frequencies for 87 selected prokaryotic BiGG models.
- `source_map_stats.tsv` - source BioEMMA map-generation statistics used by the
  reproducibility analysis.
- `source_batch_README.md` - provenance for the BiGG prokaryote map-generation
  batch.

The source maps can be regenerated with
`scripts/build_bigg_prokaryote_pathway_maps.py`. The Jaccard and reaction
frequency summaries can be rebuilt with
`scripts/compute_map_reaction_reproducibility.py`.
