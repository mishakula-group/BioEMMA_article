# Table 2. KEGG reaction mappings to SEED and BiGG

Builds a reader-facing table that counts, for every KEGG pathway in
`data/kegg_pathways.tsv` that contains at least one KEGG reaction, how many KEGG
reactions have BioEMMA/MetaNetX mappings to SEED, BiGG, either database, or
neither database.

The script uses the reaction lists already present in `data/kegg_pathways.tsv`.
It does not download KGML files from KEGG.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe tables_scripts\table_02_kegg_database_mapping\build_table_02.py
```

Outputs are written to `results/table_02_kegg_database_mapping/`.
