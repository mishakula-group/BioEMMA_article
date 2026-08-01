# Workflow files

The workflows are grouped by input type:

For the BioUML pipeline context, see the
[BioUML Flux Modeling documentation](https://biouml-flux-modeling.readthedocs.io/en/latest/index.html).

- `*_from_sequences.wdl` starts from raw FASTQ reads and runs QC, trimming,
  assembly, annotation, reconstruction, MEMOTE, and BioEMMA.
- `*_from_annotation.wdl` starts from an existing annotation/protein FASTA and
  runs reconstruction, MEMOTE, and BioEMMA.

## Files

| File | Purpose |
|---|---|
| `bactabolize_from_sequences.wdl` | Single-tool Bactabolize workflow from reads. |
| `bactabolize_from_annotation.wdl` | Single-tool Bactabolize workflow from annotation. |
| `gapseq_from_sequences.wdl` | Single-tool gapseq workflow from reads. |
| `gapseq_from_annotation.wdl` | Single-tool gapseq workflow from annotation. |
| `modelseed_from_sequences.wdl` | Single-tool ModelSEEDpy workflow from reads. |
| `modelseed_from_annotation.wdl` | Single-tool ModelSEEDpy workflow from annotation. |
| `reconstructor_from_sequences.wdl` | Single-tool Reconstructor workflow from reads. |
| `reconstructor_from_annotation.wdl` | Single-tool Reconstructor workflow from annotation. |
| `bactabolize_gapseq_modelseed_from_sequences.wdl` | Parallel Bactabolize/gapseq/ModelSEEDpy workflow from reads. |
| `bactabolize_gapseq_modelseed_from_annotation.wdl` | Parallel Bactabolize/gapseq/ModelSEEDpy workflow from annotation. |
| `gapseq_modelseed_reconstructor_from_sequences.wdl` | Article Scenario III workflow from reads; runs gapseq, ModelSEEDpy, and Reconstructor in parallel. |
| `gapseq_modelseed_reconstructor_from_annotation.wdl` | Scenario III workflow from an existing annotation. |

The article demonstration used
`gapseq_modelseed_reconstructor_from_sequences.wdl` with SRR13921546 and the
input JSON stored under `pipeline_three_reconstructors_outputs/00_workflow/`.
