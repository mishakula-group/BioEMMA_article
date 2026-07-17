version 1.0

workflow ModelReconstructionPipeline {
    input {
        File reads1
        File? reads2
        File media
        File ref_genes_fp
        File ref_proteins_fp
        File ref_model_fp
        String pathways
    }

    parameter_meta {
        reads1: "FASTQ file for forward reads"
        reads2: "FASTQ file for reverse reads (optional)"
        media: "Media file (TSV format)"
        ref_genes_fp: "GFF annotation file"
        ref_proteins_fp: "FASTA file with protein sequences"
        ref_model_fp: "Pangenome-scale model"
        pathways: "KEGG pathway map identifier (Entry number)"
   
  }

    call fastp {
        input:
            reads1 = reads1,
            reads2 = reads2
    }

    call fastqc1 {
        input:
            reads = fastp.out_reads1
    }

    if (length(fastp.out_reads2) > 0) {
    call fastqc2 {
        input:
            reads = fastp.out_reads2[0]
    }
    }

    call spades {
        input:
            reads1 = fastp.out_reads1,
            reads2 = fastp.out_reads2
    }

    call prokka {
        input:
            contigs = spades.out_folder
    }

    call bactabolize {
        input:
            fasta = spades.out_folder,
            ref_genes_fp = ref_genes_fp,
            ref_proteins_fp = ref_proteins_fp,
            ref_model_fp = ref_model_fp
    }

    call memote {
        input:
            model = bactabolize.model
    }

    call bioemma {
        input:
            model = bactabolize.model,
            pathways = pathways
    }

    call gapseq {
        input:
            fasta = spades.out_folder,
            media = media
    }

    call memote as memote_g {
        input:
            model = gapseq.model
    }

    call bioemma as bioemma_g {
        input:
            model = gapseq.model,
            pathways = pathways
    }

    call modelseed {
        input:
            fasta = prokka.out_annot,
            media = media
    }
  
    call memote as memote_m {
        input:
            model = modelseed.model
    }

    call bioemma as bioemma_m {
        input:
            model = modelseed.model,
            pathways = pathways
    }

    call memote_diff {
        input:
            model1 = bactabolize.model,
            model2 = gapseq.model,
            model3 = modelseed.model
    }

    output {
        File reads1_qc = fastqc1.out_qc
        File? reads2_qc = fastqc2.out_qc
        File model = bactabolize.model
        File model_qc = memote.out_qc
        File merged_map = bioemma.merged_map
        File all_maps = bioemma.all_maps

        File model_gp = gapseq.model
        File model_qc_gp = memote_g.out_qc
        File merged_map_gp = bioemma_g.merged_map
        File all_maps_gp = bioemma_g.all_maps

        File model_ms = modelseed.model
        File model_qc_ms = memote_m.out_qc
        File merged_map_ms = bioemma_m.merged_map
        File all_maps_ms = bioemma_m.all_maps

        File memote_diff_qc = memote_diff.out_qc
    }
}

task fastp {
    input {
        File reads1
        File? reads2
    }

    command {
        fastp -i ${reads1} ~{if defined(reads2) then "-I " + select_first([reads2]) + " -O out.R2.fq.gz" else ""} -o out.R1.fq.gz
    }

    output {
        File out_reads1 = "out.R1.fq.gz"
        Array[File] out_reads2 = glob("out.R2.fq.gz")
    }

    runtime {
            docker: "staphb/fastp:latest"
    }
}

task fastqc1 {
    input {
        File reads
    }

    command {
      ln -s ${reads} input1.fastq.gz
      mkdir output
      fastqc input1.fastq.gz -o output
    }

    output {
        File out_qc = "output/input1_fastqc.html"
    }

    runtime {
            docker: "staphb/fastqc:latest"
    }
}

task fastqc2 {
    input {
        File reads
    }

    command {
      ln -s ${reads} input2.fastq.gz
      mkdir output
      fastqc input2.fastq.gz -o output
    }

    output {
        File out_qc = "output/input2_fastqc.html"
    }

    runtime {
            docker: "staphb/fastqc:latest"
    }
}

task spades {
    input {
        File reads1
        Array[File] reads2
    }

    command {
        spades.py -1 ${reads1} ~{if length(reads2) > 0 then "-2 " + reads2[0] else ""} -o "output_folder"
    }

    output {
        File out_folder = "output_folder/scaffolds.fasta"
    }

    runtime {
            docker: "staphb/spades:3.15.5"
    }
}

task prokka {
    input {
        File contigs
    }

    command {
        prokka --outdir "output_folder" --prefix output ${contigs}
    }

    output {
        File out_annot = "output_folder/output.faa"
    }

    runtime {
            docker: "staphb/prokka:latest"
    }
}

task bactabolize {
    input {
        File fasta
        File ref_genes_fp
        File ref_proteins_fp
        File ref_model_fp
    }

    command {
        bactabolize draft_model --assembly_fp ${fasta} \
        --ref_genes_fp ${ref_genes_fp} \
        --ref_proteins_fp ${ref_proteins_fp} \
        --ref_model_fp ${ref_model_fp} \
        --biomass_reaction_id BIOMASS_Core_Oct2019 \
        --output_fp output
    }

    output {
        File model = "output_model.xml"
    }
  
    runtime {
            docker: "developmentontheedge/bactabolize:1.0.0"
    }
}

task gapseq {
    input {
        File fasta
        File media
    }

    command {
        cp ~{fasta} output.fasta
        cp ~{media} media.csv
        gapseq doall -m media.csv -t Bacteria output.fasta
    }

    output {
        File model = "output.xml"
    }
  
    runtime {
            docker: "cdiener/gapseq@sha256:eae615f0d70bee8e189c1cbef124cd795538a51a751a2e3769215f84b0e9d047"
    }
}

task modelseed {
    input {
        File fasta
        File media
    }

    command {

        export MODELSEEDPY_DATA_DIR="/tmp/modelseed_data"
        mkdir /work
        python -c 'p="/app/modelseed_gsm.py"; s=open(p).read(); s=s.replace("pd.read_csv(media)[%r, %r].values" % ("compounds", "maxFlux"), "pd.read_csv(media)[[%r, %r]].values" % ("compounds", "maxFlux")); open(p, "w").write(s)'
        python /app/modelseed_gsm.py --genome ~{fasta} --template gram- --media ~{media} --gapfill True
        cp /work/reconstructed_model.sbml ./MS_reconstructed_model.sbml
    }

    output {
        File model = "MS_reconstructed_model.sbml"
    }
  
    runtime {
            docker: "developmentontheedge/modelseed:1.0.0"
    }
}

task cobramod {
    input {
        File model
    }

    command {
      ln -s ${model} data/input_model.sbml
      cobramod_py.py
    }

    output {
        File out_model = "output_model_cobramod.sbml"
    }
  
    runtime {
            docker: "developmentontheedge/cobramod:1.0.0"
    }
}

task memote {
    input {
        File model
    }

    command {
        PYTEST_ADDOPTS='--capture=no' memote report snapshot --filename out.html ${model}
    }

    output {
        File out_qc = "out.html"
    }
  
    runtime {
            docker: "developmentontheedge/memote:latest"
    }
}

task memote_diff {
    input {
        File model1
        File model2
        File model3
    }

    command {
        PYTEST_ADDOPTS='--capture=no' memote report diff --filename out.html ${model1} ${model2} ${model3}
    }

    output {
        File out_qc = "out.html"
    }
  
    runtime {
            docker: "developmentontheedge/memote:latest"
    }
}

task bioemma {
    input {
        File model
        String pathways
    }

    command {
        WORKDIR="$(pwd)"
        cd /app/bioemma
        python /app/bioemma/main.py --model ~{model} --pathways ~{pathways}
        tar -zcf "$WORKDIR/output_maps.zip" output_maps
        cp output_maps/merged.json "$WORKDIR/merged.json"
    }

    output {
        File merged_map = "merged.json"
        File all_maps = "output_maps.zip"
    }
  
    runtime {
            docker: "developmentontheedge/bioemma:1.0.0"
    }
}
