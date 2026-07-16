# External Visualization Tools

The article comparison used several tools that are not BioEMMA itself. This repository keeps reproducible inputs, wrappers, and notes, but does not vendor third-party source trees or local environments.

- `naviflux/` - launch wrapper and API upload smoke check.
- `grohar/` - legacy setup notes.
- `sammi_networkx/` - SAMMI and NetworkX input/output generation notes.

Run the shared preparation script from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_external_tool_inputs.py --skip-optional
```
