# BiGG prokaryote BioEMMA batch

## Inputs

- BiGG model API: `http://bigg.ucsd.edu/api/v2/models`
- Model SBML files: `http://bigg.ucsd.edu/static/models/<model_id>.xml`
- Selected prokaryotic models: 88
- Excluded eukaryotic models: 20

Pathways:

- `map00010` / `rn00010`: Glycolysis / gluconeogenesis
- `map00020` / `rn00020`: Citrate cycle (TCA cycle)
- `map00030` / `rn00030`: Pentose phosphate pathway
- `map00680` / `rn00680`: Methane metabolism / C1 metabolism

## Outputs

- Source BiGG SBML URLs are retained in `../prokaryote_maps/stats/map_stats.tsv`;
  local model copies are not duplicated in this publication directory.
- `kegg_kgml/`: cached KEGG KGML files for the requested pathways.
  `*.drawable.kgml` files omit KEGG reaction entries with no x/y
  coordinates because BioEMMA cannot place them on an Escher map.
- `maps/<pathway>/<model_id>/`: BioEMMA Escher JSON and HTML maps.
- `stats/map_stats.tsv`: one row per model-pathway map.
- `stats/pathway_stats.tsv`: aggregate statistics by pathway.
- `stats/model_stats.tsv`: aggregate statistics by model.
- `stats/top_models_by_pathway.tsv`: top matched models per pathway.

## Run Summary

- Model-pathway maps successful: 352
- Model-pathway maps failed: 0



