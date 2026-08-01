version 1.0

workflow ModelReconstructionPipeline {
    input {
        File annotation
        String reconstructor_media
        String file_type = "1"
        String gram
        String pathways
    }

    parameter_meta {
        annotation: "Amino-acid FASTA or BLASTp hits file for Reconstructor"
        reconstructor_media: "Comma-separated ModelSEED compound IDs with compartment suffix for Reconstructor, for example cpd00027_e,cpd00001_e"
        file_type: "1 for amino-acid FASTA, 2 for BLASTp hits"
        gram: "positive for Gram-positive bacteria or negative for Gram-negative bacteria"
        pathways: "Comma-separated KEGG pathway entry numbers, for example 00010,00020,00030"
    }

    call reconstructor {
        input:
            input_file = annotation,
            file_type = file_type,
            gram = gram,
            media = reconstructor_media
    }

    call memote {
        input:
            model = reconstructor.model
    }

    call bioemma {
        input:
            model = reconstructor.model,
            pathways = pathways
    }

    output {
        File model = reconstructor.model
        File model_qc = memote.out_qc
        File merged_map = bioemma.merged_map
        File all_maps = bioemma.all_maps
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
