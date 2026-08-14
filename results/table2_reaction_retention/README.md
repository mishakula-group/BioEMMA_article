# Reaction retention table

This table corresponds to Table 2 in the article.

| Row | map00010 | map00020 | map00030 |
|---|---:|---:|---:|
| KEGG pathway | map00010 | map00020 | map00030 |
| Reactions in KEGG map | 56 | 29 | 59 |
| Mapped reactions | 53/56 (94.6%) | 28/29 (96.6%) | 59/59 (100.0%) |
| Retained in gapseq, n (% of KEGG map) | 32 (57.1%) | 24 (82.8%) | 39 (66.1%) |
| Retained in ModelSEED, n (% of KEGG map) | 21 (37.5%) | 18 (62.1%) | 23 (39.0%) |
| Retained in Reconstructor, n (% of KEGG map) | 32 (57.1%) | 21 (72.4%) | 26 (44.1%) |
| Reactions shared by all three models | 19 | 18 | 20 |
| Model-specific reactions | 14 | 9 | 16 |
| Matched to SEED | 53 | 28 | 59 |
| Matched to BiGG | 46 | 28 | 44 |
| Matched to both SEED and BiGG | 46 | 28 | 44 |
| Matched to either SEED or BiGG | 53 | 28 | 59 |
| Unmatched to SEED or BiGG | 3 | 1 | 0 |

## KEGG-to-database mapping split

| Row | map00010 | map00020 | map00030 |
|---|---:|---:|---:|
| KEGG reactions in map | 56 | 29 | 59 |
| Matched to SEED | 53 | 28 | 59 |
| Matched to BiGG | 46 | 28 | 44 |
| Matched to both SEED and BiGG | 46 | 28 | 44 |
| Matched to either SEED or BiGG | 53 | 28 | 59 |
| Unmatched to SEED or BiGG | 3 | 1 | 0 |

Notes:

- Mapped reactions are KEGG map reactions for which BioEMMA/MetaNetX provides at least one supported BiGG or SEED identifier.
- Retained reactions are mapped KEGG reactions that can be matched to the corresponding SBML reconstruction through KEGG, BiGG, or SEED annotations and remain in the model-filtered map.
- BioEMMA normalizes `map00010` to `rn00010` internally; the table keeps the user-facing `map00010` label.
- KGML for `map00030` contains one reaction without coordinates (`R06837`). It is counted in KEGG and mapped totals but cannot be retained on a drawable BioEMMA map.
- Detailed shared and model-specific reaction lists are written to `reaction_details.txt` and `reaction_details.json`.
- The KEGG-to-database split is written to `kegg_mapping_by_database.tsv` and `kegg_mapping_by_database.json`.
