# Table 2 reaction-retention scripts

Build the KEGG reaction-retention table from the repository root:

```powershell
.\.venv\Scripts\python.exe tables_scripts\table2_reaction_retention\build_reaction_retention_table.py
```

The script reads cached KGML files from `kgml_cache/`, compares KEGG map
reactions with the three reconstruction inputs, and writes to
`results/table2_reaction_retention/`:

- `README.md`
- `reaction_retention.tsv`
- `reaction_details.txt`
- `reaction_details.json`
- `kegg_mapping_by_database.tsv`
- `kegg_mapping_by_database.json`

