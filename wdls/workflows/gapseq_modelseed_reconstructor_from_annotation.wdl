version 1.0

workflow ModelReconstructionPipeline {
    input {
        File annotation
        File media
        String reconstructor_media
        String file_type
        String gram
        String pathways
    }
  
    parameter_meta {
        annotation: "FASTA file with nucleotide or protein sequences"
        media: "Media file (CSV/TSV format)"
        reconstructor_media: "Comma-separated ModelSEED compound IDs with compartment suffix for Reconstructor (for example cpd00027_e,cpd00001_e)"
        file_type: "File type 1-amino acid .fasta or File type 2-BLASTp hits"
        gram: "positive for Gram-positive bacteria or negative for Gram-negative bacteria"
        pathways: "KEGG pathway map identifier (Entry number)"
} 
  
    call reconstructor {
        input:
            input_file = annotation,
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
            fasta = annotation,
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
            fasta = annotation,
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
