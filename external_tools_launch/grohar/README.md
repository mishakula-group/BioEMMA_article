# Grohar

Grohar is treated as an external legacy GUI tool. This repository does not vendor the Grohar source tree or its virtual environment.

Recommended setup:

```powershell
python -m venv .grohar-venv
.\.grohar-venv\Scripts\python.exe -m pip install cobra==0.5.4 PyQt5 bioservices msgpack python-libsbml plotly pydot networkx scipy
```

The original Grohar workflow also expects Graphviz and an LP solver such as Gurobi. Without them, GUI and structural visualization may still import, but optimization workflows can fail.

Input model for reproducing the article comparison:

```text
data/e_coli_core.xml
```

The supplementary workflow notes in `figures_scripts/supplementary_figures/supplementary_tool_workflows.md` describe the fallback NetworkX route used when the GUI workflow is inconvenient.

