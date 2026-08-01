# KEGG database mapping analysis

This folder contains the pathway-wide KEGG-to-SEED/BiGG mapping analysis
discussed in the article limitations section.

Files:

- `kegg_database_mapping_all_pathways.md` - reader-facing Markdown table.
- `kegg_database_mapping_all_pathways.tsv` - tabular data.
- `kegg_database_mapping_all_pathways.json` - structured data with the same
  counts.

The table includes the 153 KEGG pathways from `../../data/kegg_pathways.tsv`
that contain at least one KEGG reaction. It does not download KGML files from
KEGG during generation.
