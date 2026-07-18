Pipeline outputs for three metabolic reconstructors
===================================================

Dataset
-------
- Organism: Escherichia coli str. K-12 substr. MG1655
- SRA run: SRR13921546
- BioProject: PRJNA706563
- Medium: M9_vit_aa.csv
- Reconstructors: gapseq, ModelSEED, Reconstructor
- KEGG maps: 00010, 00020, 00030

Contents
--------
- 00_workflow/: WDL and input JSON for the three-reconstructor workflow.
- 01_input_medium/: medium file used for reconstruction.
- 02_raw_read_qc/: FastQC reports for the input read pairs.
- 03_trimmed_reads_and_qc/: processed paired reads, fastp report, and FastQC reports after trimming.
- 04_assembly/: SPAdes assembly outputs.
- 05_assembly_qc/: QUAST assembly quality report.
- 06_annotation/: Prokka annotation outputs.
- 07_gapseq_model/: gapseq model outputs and reaction/pathway/transport tables.
- 08_modelseed_model/: ModelSEED reconstructed model.
- 09_reconstructor_model/: Reconstructor reconstructed model.
- 10_memote_reports/: memote reports for the three reconstructed models and the comparison report.
- 11_bioemma_maps/: pathway map archive.
- 12_final_models/: renamed final models for direct use.

Notes
-----
Raw input FASTQ files are not included. The archive includes the processed reads generated
by the read-processing stage and the outputs needed to inspect each downstream stage.
