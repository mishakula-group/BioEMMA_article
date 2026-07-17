version 1.0

workflow ModelReconstructionPipeline {
    input {
        File annotation
        File media
        String pathways
    }
        
    parameter_meta {
        annotation: "FASTA file with nucleotide or protein sequences"
        media: "Media file (CSV/TSV format)"
        pathways: "KEGG pathway map identifier (Entry number)"
    }

    call gapseq {
        input:
            fasta = annotation,
            media = media
    }

    call cobramod {
        input:
            model = gapseq.model
    }
  
    call memote {
        input:
            model = cobramod.out_model
    }

    call bioemma {
        input:
            model = cobramod.out_model,
            pathways = pathways
    }

    output {
        File model = cobramod.out_model
        File model_qc = memote.out_qc
        File merged_map = bioemma.merged_map
        File all_maps = bioemma.all_maps
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
