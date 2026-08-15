# E. coli Reaction Reproducibility Metrics

Source maps: `results/prokaryote_maps/maps`
Models: 57 BiGG Escherichia coli models; `e_coli_core` excluded.

Jaccard is calculated over KEGG reaction IDs that are actually present in each generated Escher JSON map.
BiGG/model reaction IDs are retained in the long/frequency tables as supporting identifiers.

Files:
- `ecoli_map_reactions_long.tsv`: one row per drawn reaction per model-pathway map.
- `ecoli_map_reaction_counts.tsv`: drawn KEGG reaction set and count per model-pathway.
- `ecoli_pairwise_jaccard.tsv`: pairwise Jaccard metrics for every model pair within each pathway.
- `ecoli_pairwise_reaction_differences.tsv`: reaction IDs unique to either model for non-identical pairs.
- `ecoli_jaccard_summary_by_pathway.tsv`: compact Jaccard/count summary by pathway.
- `ecoli_reaction_frequency_by_pathway.tsv`: core/variable reaction frequency across E. coli models.
- `ecoli_mapping_metrics_by_model_pathway.tsv`: original BioEMMA mapping metrics subset for these models.
- `ecoli_mapping_metric_summary_by_pathway.tsv`: mapping metric summary by pathway.
