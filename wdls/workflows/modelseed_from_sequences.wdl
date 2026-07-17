version 1.0

workflow ModelReconstructionPipeline {
    input {
        File reads1
        File? reads2
        File media
        String pathways
    }
  
    parameter_meta {
        reads1: "FASTQ file for forward reads"
        reads2: "FASTQ file for reverse reads (optional)"
        media: "Media file (TSV format)"
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
  
    call modelseed {
        input:
            fasta = prokka.out_annot,
            media = media
    }

    #call cobramod {
      #  input:
        #    model = modelseed.model
    #}
  
    call memote {
        input:
            model = modelseed.model
    }

    call bioemma {
        input:
            model = modelseed.model,
            pathways = pathways
    }

    output {
        File reads1_qc = fastqc1.out_qc
        File? reads2_qc = fastqc2.out_qc
        File reads3_qc = fastqc3.out_qc
        File? reads4_qc = fastqc4.out_qc
        File trimmed1 = fastp.out_reads1
        Array[File] trimmed2 = fastp.out_reads2
        Array[File] spades_outputs = spades.all_outputs
        Array[File] quast_outputs = quast.all_outputs
        Array[File] prokka_outputs = prokka.all_outputs
        File model = modelseed.model
        File model_qc = memote.out_qc
        File merged_map = bioemma.merged_map
        File all_maps = bioemma.all_maps
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

#task cobramod {
#    input {
#        File model
#    }

    #command {
    #  ln -s ~{model} data/input_model.sbml
    #  cobramod_py.py
    #}

    #output {
    #    File out_model = "output_model_cobramod.sbml"
    #}
  
    #runtime {
     #       docker: "developmentontheedge/cobramod:1.0.0"
    #}
#}

task memote {
    input {
        File model
    }

    command {
        mkdir memote
        PYTEST_ADDOPTS='--capture=no' memote report snapshot --filename memote/report.html ~{model}
    }

    output {
        File out_qc = "memote/report.html"
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
