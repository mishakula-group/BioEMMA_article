# Table 1

Build the KEGG reaction-retention table from the repository root:

```powershell
.\.venv\Scripts\python.exe figures\table_01\build_table_01.py
```

The script reads cached KGML files from `kgml_cache/`, compares KEGG map reactions with the three Figure 3 reconstruction inputs, and writes:

- `README.md`
- `table_01.tsv`
- `table_01_reaction_details.txt`
- `table_01_reaction_details.json`
