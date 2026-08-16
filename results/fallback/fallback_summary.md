# BioEMMA 0.4.2 fallback summary

BioEMMA 0.4.2 keeps the BiGG EC fallback from 0.4.1 and adds a separate SEED EC fallback layer.

## Resource coverage

| Metric | 0.4.1 | 0.4.2 | Delta |
|---|---:|---:|---:|
| KEGG reaction rows | 11863 | 11863 | 0 |
| BiGG coverage | 3786 | 3786 | 0 |
| SEED coverage | 7363 | 9916 | 2553 |
| BiGG EC fallback rows | 2046 | 2046 | 0 |
| SEED EC fallback rows | 0 | 2553 | 2553 |

## Fallback overlap

- BiGG EC fallback reactions: `2046`.
- SEED EC fallback reactions: `2553`.
- Overlap: `662` reactions (25.9% of SEED fallback, 32.4% of BiGG fallback).
- SEED-only fallback reactions: `1891`.
- BiGG-only fallback reactions: `1384`.

## Validation snapshots

| Test | Sources | Exact | Mixed hit | Wrong only | Miss | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BiGG MNX participants inclusive best-ties | 1711 | 1697 | 14 | 0 | 0 | 0.934 | 1.000 | 0.966 |
| BiGG KEGG formula inclusive best-ties | 1704 | 1668 | 36 | 0 | 0 | 0.907 | 1.000 | 0.951 |
| SEED MNX participants inclusive best-ties | 6575 | 6521 | 54 | 0 | 0 | 0.889 | 1.000 | 0.941 |
| SEED KEGG formula inclusive best-ties | 6549 | 6258 | 286 | 3 | 2 | 0.757 | 0.999 | 0.862 |
| SEED KEGG formula leave-one-MNX-out best-ties | 6549 | 0 | 0 | 4135 | 2414 | 0.000 | 0.000 | 0.000 |

## Article-map impact

- Fresh EC baseline vs SEED fallback changed maps: `0`.
- Fresh EC baseline vs SEED fallback changed flux JSON files: `0`.
- Therefore article maps were copied from the 0.4.1 bundle instead of regenerated here.

Source evidence is in `map_nochange_evidence/regen_comparison.md`.

