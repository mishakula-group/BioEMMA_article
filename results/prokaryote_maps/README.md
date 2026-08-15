# BiGG prokaryote BioEMMA batch

Generated at: 2026-08-12 02:22:19 +0300

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

- `maps/<pathway>/<model_id>/`: BioEMMA Escher JSON and HTML maps.
- `stats/map_stats.tsv`: one row per model-pathway map.
- `stats/pathway_stats.tsv`: aggregate statistics by pathway.
- `stats/model_stats.tsv`: aggregate statistics by model.
- `stats/top_models_by_pathway.tsv`: top matched models per pathway.
- `inventory/`: BiGG model inventory and prokaryote/eukaryote filtering table.
- `kegg_kgml/`: cached KEGG KGML files for the requested pathways.
  `*.drawable.kgml` files omit KEGG reaction entries with no x/y
  coordinates because BioEMMA cannot place them on an Escher map.

Downloaded BiGG SBML files are not duplicated in this publication results
folder because they account for most of the batch size. The corresponding
source model URL is retained in the `model_xml` column of `stats/map_stats.tsv`.

## Run Summary

- Model-pathway maps successful: 352
- Model-pathway maps failed: 0

Classification note: BiGG's model-list endpoint does not include a domain
field, so this batch keeps all models except organism strings matching
the known eukaryotic taxa currently present in the BiGG list.

## Environment and timing

- BioEMMA before environment update: `0.2.0`.
- BioEMMA after environment update: `0.4.0`.
- Editable source commit: `f8a2a3260777499842a19e923ab12197152d9f81`.
- Full rerun wall-clock time: `00:17:36` (1056.921 seconds).
- Timing metadata: `run_metadata.json`.
- Comparison against the previous run: `stats/pathway_stats_vs_previous.tsv`.
