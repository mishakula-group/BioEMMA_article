# Table 1. Retention of KEGG map reactions in reconstructions

| Row | map00010 | map00020 | map00030 |
|---|---:|---:|---:|
| KEGG pathway | map00010 | map00020 | map00030 |
| Reactions in KEGG map | 56 | 29 | 59 |
| Mapped reactions | 47/56 (83.9%) | 21/29 (72.4%) | 55/59 (93.2%) |
| Retained in gapseq, n (% of KEGG map) | 28 (50.0%) | 17 (58.6%) | 35 (59.3%) |
| Retained in ModelSEED, n (% of KEGG map) | 18 (32.1%) | 11 (37.9%) | 23 (39.0%) |
| Retained in Reconstructor, n (% of KEGG map) | 28 (50.0%) | 14 (48.3%) | 26 (44.1%) |
| Reactions shared by all three models | 16 | 11 | 20 |
| Model-specific reactions | 12 | 9 | 14 |

Notes:

- Mapped reactions are KEGG map reactions for which BioEMMA/MetaNetX provides at least one supported BiGG or SEED identifier.
- Retained reactions are mapped KEGG reactions that can be matched to the corresponding SBML reconstruction through KEGG, BiGG, or SEED annotations and remain in the model-filtered map.
- BioEMMA normalizes `map00010` to `rn00010` internally; the table keeps the user-facing `map00010` label.
- KGML for `map00030` contains one reaction without coordinates (`R06837`). It is counted in KEGG and mapped totals but cannot be retained on a drawable BioEMMA map.
- Detailed shared and model-specific reaction lists are written to `table_01_reaction_details.txt` and `table_01_reaction_details.json`.
