version 1.0

workflow ModelReconstructionPipeline {
    input {
        File reads1
        File? reads2
        File media
        String reconstructor_media
        String file_type = "1"
        String gram
        String pathways
    }
  
    parameter_meta {
        reads1: "FASTQ file for forward reads"
        reads2: "FASTQ file for reverse reads (optional)"
        media: "Media file (CSV/TSV format)"
        reconstructor_media: "Comma-separated ModelSEED compound IDs with compartment suffix for Reconstructor (for example cpd00027_e,cpd00001_e)"
        file_type: "Amino acid .fasta"
        gram: "positive for Gram-positive bacteria or negative for Gram-negative bacteria"
        pathways: "KEGG pathway map identifier (Entry number)"
    
  }
  
    call fastqc1 {
        input:
            reads = reads1
    }
  
    if (defined(reads2)) {
    call fastqc2 {
        input:
            reads = select_first([reads2])
    }
    }
  
    call fastp {
        input:
            reads1 = reads1,
            reads2 = reads2
    }
  
    call fastqc3 {
        input:
            reads = fastp.out_reads1
    }
  
    if (length(fastp.out_reads2) > 0) {
    call fastqc4 {
        input:
            reads = fastp.out_reads2[0]
    }
    }
  
    call spades {
        input:
            reads1 = fastp.out_reads1,
            reads2 = fastp.out_reads2
    }
    
    call quast {
        input:
            scaffolds = spades.scaffolds
    }

    call prokka {
        input:
            scaffolds = spades.scaffolds
    }
  
    call reconstructor {
        input:
            input_file = prokka.out_annot,
            file_type = file_type,
            gram = gram,
            media = reconstructor_media
    }

#    call cobramod {
#        input:
#            model = reconstructor.model
#    }
  
    call memote {
        input:
            model = reconstructor.model
    }

    call bioemma {
        input:
            model = reconstructor.model,
            pathways = pathways
    }

    call gapseq {
        input:
            fasta = prokka.out_annot,
            media = media
    }

#    call cobramod as cobramod_g {
#        input:
#            model = gapseq.model
#    }
  
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

#    call cobramod as cobramod_m {
#        input:
#            model = modelseed.model
#    }
  
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
            model1 = reconstructor.model,
            model2 = gapseq.model,
            model3 = modelseed.model
    }

    output {
        File model = reconstructor.model
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

task fastqc1 {
    input {
        File reads
    }

    command {
      ln -s ~{reads} input1.fastq.gz
      mkdir fastQC_report
      fastqc input1.fastq.gz \
      -o fastQC_report
    }

    output {
        File out_qc = "fastQC_report/input1_fastqc.html"
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
      ln -s ~{reads} input2.fastq.gz
      mkdir fastQC_report
      fastqc input2.fastq.gz \
      -o fastQC_report
    }

    output {
        File out_qc = "fastQC_report/input2_fastqc.html"
    }
  
    runtime {
            docker: "staphb/fastqc:latest"
    }
}

task fastp {
    input {
        File reads1
        File? reads2
    }

    command {
        fastp -i ~{reads1} ~{if defined(reads2) then "-I " + select_first([reads2]) + " -O trimmed.R2.fq.gz" else ""} -o trimmed.R1.fq.gz
    }

    output {
        File out_reads1 = "trimmed.R1.fq.gz"
        Array[File] out_reads2 = glob("trimmed.R2.fq.gz")
    }
  
    runtime {
            docker: "staphb/fastp:latest"
    }
}

task fastqc3 {
    input {
        File reads
    }

    command {
      ln -s ~{reads} trimmed_input1.fastq.gz
      mkdir fastQC_report
      fastqc trimmed_input1.fastq.gz \
      -o fastQC_report
    }

    output {
        File out_qc = "fastQC_report/trimmed_input1_fastqc.html"
    }
  
    runtime {
            docker: "staphb/fastqc:latest"
    }
}

task fastqc4 {
    input {
        File reads
    }

    command {
      ln -s ~{reads} trimmed_input2.fastq.gz
      mkdir fastQC_report
      fastqc trimmed_input2.fastq.gz \
      -o fastQC_report
    }

    output {
        File out_qc = "fastQC_report/trimmed_input2_fastqc.html"
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
        spades.py -1 ~{reads1} \
        ~{if length(reads2) > 0 then "-2 " + reads2[0] else ""} \
        -o "spades_output"
        find $(pwd)/spades_output -type f > outputs.txt
    }

    output {
        #File contigs = "spades_output/contigs.fasta"
        File scaffolds = "spades_output/scaffolds.fasta"
        #File spades_logs = "spades_output/spades.log"
        #File params = "spades_output/params.txt"
        #File broken_scaffolds = "spades_output/misc/broken_scaffolds.fasta"
        Array[File] all_outputs = read_lines("outputs.txt")
    }
  
    runtime {
            docker: "staphb/spades:3.15.5"
    }
}

task quast {
    input {
        File scaffolds
    }

    command {
        quast.py ${scaffolds} -o quast_report
        find $(pwd)/quast_report -type f > outputs.txt
    }

    output { 
        Array[File] all_outputs = read_lines("outputs.txt")
        
    }
  
    runtime {
            docker: "staphb/quast:latest"
    }
}

task prokka {
    input {
        File scaffolds
    }

    command {
        prokka --outdir "prokka_annotation" --prefix output ~{scaffolds}
        find $(pwd)/prokka_annotation -type f > outputs.txt
    }

    output {
        File out_annot = "prokka_annotation/output.faa"
        Array[File] all_outputs = read_lines("outputs.txt")
    }
  
    runtime {
            docker: "staphb/prokka:latest"
    }
}

task reconstructor {
    input {
        File input_file
        String file_type
        String gram
        String media
    }

    command {
      
        mkdir reconstructor
        python -m reconstructor --input_file ~{input_file} \
        --file_type ~{file_type} \
        --gram ~{gram} \
        --media ~{media} \
        --out reconstructor/model.sbml
        
    }

    output {
            File model = "reconstructor/model.sbml"
    }
  
    runtime {
        docker: "developmentontheedge/reconstructor:1.0.0"
    }
}

task gapseq {
    input {
        File fasta
        File media
    }

    command {
        cp ~{fasta} output.fna
        cp ~{media} media.csv
        chmod 777 output.fna
        gapseq doall -m media.csv -t Bacteria output.fna
        
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
        python /app/modelseed_gsm.py --genome ~{fasta} --media ~{media} --gapfill True
        ls -la /work
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
        mkdir memote
        PYTEST_ADDOPTS='--capture=no' memote report snapshot --filename memote/report.html ${model}
    }

    output {
        File out_qc = "memote/report.html"
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
        mkdir memote
        PYTEST_ADDOPTS='--capture=no' memote report diff --filename memote/out.html ${model1} ${model2} ${model3}
    }

    output {
        File out_qc = "memote/out.html"
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
        python /app/bioemma/main.py --model ~{model} --pathways ~{pathways} || true
        tar -zcf "$WORKDIR/output_maps.zip" output_maps
        if [ -f output_maps/merged.json ]; then
            cp output_maps/merged.json "$WORKDIR/merged.json"
        else
            echo '{"warning":"BioEMMA did not produce merged.json; see output_maps.zip for individual pathway maps"}' > "$WORKDIR/merged.json"
        fi
    }

    output {
        File merged_map = "merged.json"
        File all_maps = "output_maps.zip"
    }
  
    runtime {
            docker: "developmentontheedge/bioemma:1.0.0"
    }
}
