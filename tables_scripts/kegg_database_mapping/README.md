# KEGG reaction mappings to SEED and BiGG

Builds the pathway-wide mapping table discussed in the article limitations.

The script counts, for every KEGG pathway in `data/kegg_pathways.tsv` that
contains at least one KEGG reaction, how many KEGG reactions have
BioEMMA/MetaNetX mappings to SEED, BiGG, either database, or neither database.
It uses the reaction lists already present in `data/kegg_pathways.tsv` and does
not download KGML files from KEGG.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe tables_scripts\kegg_database_mapping\build_kegg_database_mapping.py
```

Outputs are written to `results/table_02_kegg_database_mapping/`. That results
path is kept because it is cited directly in the article.
