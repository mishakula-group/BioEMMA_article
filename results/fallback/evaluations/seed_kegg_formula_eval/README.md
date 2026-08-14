# SEED fallback check with KEGG reaction formulas

This is the KEGG-formula version of the SEED EC fallback audit.

Protocol:

1. Build the direct KEGG -> SEED gold table from the fresh MetaNetX reaction
   cross-reference and reaction-property files used for the BioEMMA resource
   build.
2. Take only gold reactions with direct SEED mapping and EC numbers.
3. Fetch KEGG reaction entries through KEGG REST and parse the KEGG
   `EQUATION` field.
4. Convert KEGG compounds from the equation to MNX compounds with
   `metanetx_data/chem_xref.tsv`.
5. Pretend the direct KEGG -> SEED mapping is unavailable and predict SEED IDs
   through EC number plus participant overlap threshold `>= 0.50`.
6. Evaluate both inclusive matching and leave-one-MNX-out matching.

Inputs:

- Direct KEGG -> SEED rows: 7363
- Direct KEGG -> SEED rows with EC: 6575
- Evaluated rows with KEGG equation -> MNX participants: 6549
- Skipped rows: 12 without KEGG equation, 14 without MNX participants
- KEGG compounds parsed from equations: 28610
- KEGG compounds not mapped to MNX: 3341

Main result, inclusive best-overlap ties:

- Recovered any correct SEED ID: 6544 / 6549 = 99.9%
- Exact reaction-level match: 6258
- Mixed hit: 286
- Wrong only: 3
- Miss: 2
- Label-level confusion matrix: TP=9975, FP=3195, FN=5, TN=191800486
- Precision: 0.757
- Recall: 0.999
- F1: 0.862

Strict leave-one-MNX-out result:

- Recovered any correct SEED ID: 0 / 6549 = 0.0%
- Wrong only: 4135
- Miss: 2414

Interpretation:

The KEGG-formula inclusive check confirms that the SEED fallback reproduces
almost all known KEGG -> SEED links when the source reaction itself remains in
the EC candidate pool. The strict leave-one-MNX-out check is intentionally much
harsher and gives 0 recovery, meaning the successful inclusive recovery is
mostly recovery of the same MetaNetX reaction record rather than independent
discovery from a different MNX record.

Detailed output:

- `seed_kegg_formula_fallback_confusion.json`
- `kegg_reaction_entries.json`
