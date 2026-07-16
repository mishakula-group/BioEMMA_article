# BioEMMA Notes From Figure 1

These are issues surfaced while preparing the rn00010 / e_coli_core article figure. The goal is to move as much of this out of article-material glue code and into BioEMMA itself.

## Library Issues

1. Submap extraction is currently external glue code.
   A first-class BioEMMA API for cropping/extracting a map fragment would be useful, but it should be framed as "extract a pathway subgraph", not as a screenshot crop. Useful controls: anchor reactions/metabolites, graph radius, optional coordinate bounds, include/exclude lists, orphan cleanup, canvas retuning, and validation.

2. Coordinate-only cropping pulls in unrelated side branches.
   The rn00010 fragment around ENO/PYK also captured left-side KEGG branches and LDH_L because their segments pass through the same coordinate window. A graph-neighborhood crop would be more biologically meaningful than a pure bounding box.

3. KEGG-only metabolites can render with blank labels.
   Example: C01159 had no mapped BiGG ID, so Escher rendered the node without a useful visible label. BioEMMA should provide a display-label fallback, likely BiGG -> common name -> KEGG ID.

4. Stereochemistry-aware reaction mapping needs clearer diagnostics.
   KEGG rn00010 contains LDH_L / R00703, while e_coli_core contains LDH_D / R00704. The tool behaves correctly by not matching them, but the summary should explain unmatched close analogs so the user does not think LDH is missing.

5. Reaction aliases remain article-side knowledge.
   BioEMMA maps KEGG R01518 to PGAM_h, while the e_coli_core flux table uses PGM. This kind of aliasing should be exposed through mapping diagnostics or a supported user override file.

6. HTML export requires Escher but BioEMMA does not install it directly.
   Either make `escher` an explicit dependency, add an optional extra such as `bioemma[html]`, or make the error message point to the required install command.

## Is Cropping Useful In BioEMMA?

Yes, probably, if it is implemented as reproducible submap extraction rather than manual figure cropping. It would help for article figures, notebooks, debugging model/pathway overlap, and teaching examples. The default should avoid silently changing biological content: return the retained and discarded reactions, explain why each was kept/removed, and validate the resulting Escher map.
