# Fallback validation materials

This directory contains the BioEMMA 0.4.2 EC-fallback validation and resource
coverage materials used to document the BiGG and ModelSEED/SEED fallback
behavior.

Key files:

- `fallback_summary.md` and `fallback_summary.json` - compact fallback coverage,
  validation, and article-map impact summary.
- `evaluations/ec_fallback_eval/` - BiGG EC-fallback validation details.
- `evaluations/seed_fallback_eval/` - SEED EC-fallback validation details.
- `evaluations/seed_kegg_formula_eval/` - SEED EC-fallback validation using
  KEGG reaction equations as the participant source.
- `map_nochange_evidence/` - comparison showing that adding SEED fallback did
  not change the tested article maps or flux JSON files.
- `resources_0_4_1/` and `resources_0_4_2/` - reaction-mapping resource
  snapshots used for the fallback comparison.
- `table2_seed_vs_bigg_fallback/` and
  `kegg_database_mapping_seed_vs_bigg_fallback/` - table-oriented fallback
  contribution summaries.

The compact fallback summary can be rebuilt with
`scripts/build_fallback_summary.py`.

