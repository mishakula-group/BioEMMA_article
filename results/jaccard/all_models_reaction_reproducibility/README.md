# Reaction Reproducibility Metrics

Source maps: `outputs\bigg_prokaryote_bioemma`
Models: 87 BiGG prokaryotic models; excluded: `e_coli_core`.

Jaccard is calculated over KEGG reaction IDs that are actually present in each generated Escher JSON map.
BiGG/model reaction IDs are retained in the long/frequency tables as supporting identifiers.

Files:
- `all_models_map_reactions_long.tsv`: one row per drawn reaction per model-pathway map.
- `all_models_map_reaction_counts.tsv`: drawn KEGG reaction set and count per model-pathway.
- `all_models_pairwise_jaccard.tsv`: pairwise Jaccard metrics for every model pair within each pathway.
- `all_models_pairwise_reaction_differences.tsv`: reaction IDs unique to either model for non-identical pairs.
- `all_models_jaccard_summary_by_pathway.tsv`: compact Jaccard/count summary by pathway.
- `all_models_reaction_frequency_by_pathway.tsv`: core/variable reaction frequency across selected models.
- `all_models_mapping_metrics_by_model_pathway.tsv`: original BioEMMA mapping metrics subset for these models.
- `all_models_mapping_metric_summary_by_pathway.tsv`: mapping metric summary by pathway.
