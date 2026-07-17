version 1.0

workflow ModelReconstructionPipeline {
    input {
        File annotation
        File media
        String pathways = "00010"
    }
  
    parameter_meta {
        annotation: "FASTA file with nucleotide sequences"
        media: "Media file (TSV format)"
        pathways: "KEGG pathway map identifier (Entry number)"
   
  }
  
    call modelseed {
        input:
            fasta = annotation,
            media = media
    }

#    call cobramod {
#        input:
#            model = modelseed.model
#    }
  
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
        File model = modelseed.model
        File model_qc = memote.out_qc
        File merged_map = bioemma.merged_map
        File all_maps = bioemma.all_maps
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
