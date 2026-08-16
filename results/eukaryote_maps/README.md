# BiGG eukaryote BioEMMA no-fallback batch

This directory contains the no-fallback BioEMMA maps used for the selected
eukaryotic model comparison in Supplementary Table S3.

## Inputs

- Models: `iMM904` (`Saccharomyces cerevisiae S288C`), `iMM1415`
  (`Mus musculus`), and `Recon3D` (`Homo sapiens`).
- Pathways: `map00010`, `map00020`, `map00030`, and `map00680`.
- Mapping mode: EC-number-only fallback aliases excluded from BiGG/SEED
  matching.

## Outputs

- `models/` - retained SBML model copies.
- `maps/<pathway>/<model_id>/` - BioEMMA Escher JSON and HTML maps.
- `stats/map_stats.tsv` and `stats/map_stats.json` - one row per
  model-pathway map.
- `stats/pathway_stats.tsv` and `stats/model_stats.tsv` - aggregate statistics.
- `stats/top_models_by_pathway.tsv` and `stats/top_models_by_pathway.json` -
  retained-reaction ranking by pathway.

The corresponding pairwise Jaccard summaries are in
`../jaccard/eukaryotic_model_reproducibility/`.
