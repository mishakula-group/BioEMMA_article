# SEED EC fallback validation

Date: 2026-08-14

This directory contains the MNX-participant SEED EC-fallback validation details.
The stricter KEGG-equation validation is stored in
`../seed_kegg_formula_eval/` and is used as the main SEED validation snapshot in
the compact fallback summary.

The tested rule mirrors the BiGG EC fallback: KEGG reactions without direct
SEED mapping are matched to candidate SEED reactions sharing the same EC number,
and candidates are retained when participant overlap is at least 50%. Tied
best-overlap candidates are retained as ambiguous fallback-derived mappings.

Files:

- `seed_fallback_confusion.json` - SEED fallback evaluation details.

Main numbers:

- total KEGG reaction rows: `11863`;
- direct SEED before fallback: `7363`;
- SEED after fallback: `9916`;
- added by SEED fallback: `2553`;
- BiGG after existing EC fallback: `3786`.

Leave-one-out check on rows with direct KEGG-to-SEED mapping, EC annotation, and
participants:

- gold rows: `6575`;
- inclusive best-ties: recovered `6575/6575`, label precision `0.889`, recall
  `1.000`;
- strict leave-one-MNX-out: recovered `0/6575`.

The strict leave-one-MNX-out result is a conservative stress test: once the
source MNX record is removed, the true alias usually disappears with it. The
article-map comparison in `../../map_nochange_evidence/` showed `0` changed
Escher maps and `0` changed flux JSON files after adding SEED fallback.

