# Table 2: current BiGG fallback vs temporary SEED fallback

## Changed Table 2 rows

| Row | map00010 | map00020 | map00030 |
|---|---:|---:|---:|
| Mapped reactions | 51/56 (91.1%) -> 53/56 (94.6%) | 28/29 (96.6%) -> 28/29 (96.6%) | 56/59 (94.9%) -> 59/59 (100.0%) |
| Retained in gapseq, n (% of KEGG map) | 32 (57.1%) -> 32 (57.1%) | 23 (79.3%) -> 24 (82.8%) | 38 (64.4%) -> 39 (66.1%) |
| Retained in ModelSEED, n (% of KEGG map) | 18 (32.1%) -> 21 (37.5%) | 11 (37.9%) -> 18 (62.1%) | 23 (39.0%) -> 23 (39.0%) |
| Retained in Reconstructor, n (% of KEGG map) | 28 (50.0%) -> 32 (57.1%) | 14 (48.3%) -> 21 (72.4%) | 26 (44.1%) -> 26 (44.1%) |
| Reactions shared by all three models | 16 -> 19 | 11 -> 18 | 20 -> 20 |
| Model-specific reactions | 16 -> 14 | 15 -> 9 | 15 -> 16 |
| Matched to SEED | 47 -> 53 | 21 -> 28 | 55 -> 59 |
| Matched to both SEED and BiGG | 42 -> 46 | 21 -> 28 | 43 -> 44 |
| Matched to either SEED or BiGG | 51 -> 53 | 28 -> 28 | 56 -> 59 |
| Unmatched to SEED or BiGG | 5 -> 3 | 1 -> 1 | 3 -> 0 |

## KEGG-to-database split delta

| Pathway | Metric | BiGG fallback | SEED fallback | Added | Removed |
|---|---|---:|---:|---|---|
| map00010 | seed_mapped | 47 | 53 | R02569, R03270, R05198, R07618, R09127, R09479 | - |
| map00010 | both_bigg_and_seed | 42 | 46 | R02569, R03270, R05198, R07618 | - |
| map00010 | either_bigg_or_seed | 51 | 53 | R09127, R09479 | - |
| map00010 | unmapped_to_bigg_or_seed | 5 | 3 | - | R09127, R09479 |
| map00010 | drawable_seed_mapped | 47 | 53 | R02569, R03270, R05198, R07618, R09127, R09479 | - |
| map00010 | drawable_either | 51 | 53 | R09127, R09479 | - |
| map00020 | seed_mapped | 21 | 28 | R00361, R02164, R02569, R02570, R03270, R03316, R07618 | - |
| map00020 | both_bigg_and_seed | 21 | 28 | R00361, R02164, R02569, R02570, R03270, R03316, R07618 | - |
| map00020 | drawable_seed_mapped | 21 | 28 | R00361, R02164, R02569, R02570, R03270, R03316, R07618 | - |
| map00030 | seed_mapped | 55 | 59 | R00305, R06620, R10324, R10907 | - |
| map00030 | both_bigg_and_seed | 43 | 44 | R10907 | - |
| map00030 | either_bigg_or_seed | 56 | 59 | R00305, R06620, R10324 | - |
| map00030 | unmapped_to_bigg_or_seed | 3 | 0 | - | R00305, R06620, R10324 |
| map00030 | drawable_seed_mapped | 54 | 58 | R00305, R06620, R10324, R10907 | - |
| map00030 | drawable_either | 55 | 58 | R00305, R06620, R10324 | - |
