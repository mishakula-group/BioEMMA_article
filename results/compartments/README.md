# Compartment-specific eukaryotic maps

This directory contains BioEMMA compartment-specific maps for three eukaryotic
genome-scale metabolic models: yeast `iMM904`, mouse `iMM1415`, and human
`Recon3D`.

Key files:

- `index.html` and `index.json` - entry points summarizing all generated
  compartment maps.
- `timing.csv` and `timing.json` - model loading, FBA, and map-building timing
  summaries.
- `yeast_iMM904/`, `mouse_iMM1415/`, and `human_Recon3D/` - model-specific
  pathway maps, compartment submaps, flux tables, and per-pathway summaries.

The maps can be regenerated with `scripts/build_compartment_maps.py`. Pass
`--source-root` or set `BIOEMMA_COMPARTMENT_SOURCE_ROOT` to the folder
containing the corresponding SBML models and KGML files.
