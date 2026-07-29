# WDL workflows

This folder contains the WDL files used to expose the BioEMMA article pipeline
scenarios outside the BioUML web interface. The workflows are written for
Cromwell/WDL v1 execution and use Docker images for each pipeline tool.

## Article run

The article test case for comparing three reconstructions used:

- WDL: `workflows/gapseq_modelseed_reconstructor_from_sequences.wdl`
- Inputs: `../pipeline_three_reconstructors_outputs/00_workflow/e_coli_gapseq_modelseed_reconstructor.inputs.json`
- Dataset: SRA run `SRR13921546`, BioProject `PRJNA706563`
- Medium: `../data/M9_vit_aa.csv`
- Gram setting: `negative`
- KEGG pathways: `00010,00020,00030`
- Reconstructors: gapseq, ModelSEEDpy, Reconstructor

Example Cromwell command from the repository root:

```powershell
java -jar cromwell.jar run wdls\workflows\gapseq_modelseed_reconstructor_from_sequences.wdl -i pipeline_three_reconstructors_outputs\00_workflow\e_coli_gapseq_modelseed_reconstructor.inputs.json
```

The JSON contains placeholder FASTQ paths because raw SRA reads are not stored
in this repository. Download `SRR13921546_1.fastq.gz` and
`SRR13921546_2.fastq.gz` locally, then replace those two paths before running.

## Medium parameters

`../data/M9_vit_aa.csv` is the ModelSEED-style medium table used for
gapseq and ModelSEEDpy. Reconstructor expects the same medium as a comma
separated string of extracellular ModelSEED compound IDs; the article input JSON
uses the first column of `M9_vit_aa.csv` with `_e` appended to each compound ID.

## Generated outputs

Cromwell working directories and generated folders named `outputs/` are ignored
by git. Curated outputs that are used by the article are copied into `results/`.
