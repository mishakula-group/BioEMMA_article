version 1.0

workflow ModelReconstructionPipeline {
    input {
        File fasta
        File ref_genes_fp
        File ref_proteins_fp
        File ref_model_fp
        String pathways
    }
        
    parameter_meta {
        fasta: "Assembled FASTA file"
        ref_genes_fp: "GFF annotation file"
        ref_proteins_fp: "FASTA file with protein sequences"
        ref_model_fp: "Pangenome-scale model"
        pathways: "KEGG pathway map identifier (Entry number)"
        
        
  }
  
    call bactabolize {
        input:
            fasta = fasta,
            ref_genes_fp = ref_genes_fp,
            ref_proteins_fp = ref_proteins_fp,
            ref_model_fp = ref_model_fp
    }

#    call cobramod {
#        input:
#            model = bactabolize.model
#    }
  
    call memote {
        input:
            model = bactabolize.model
    }

    call bioemma {
        input:
            model = bactabolize.model,
            pathways = pathways
    }

    output {
#        File model = cobramod.out_model
        File model = bactabolize.model
        File model_qc = memote.out_qc
        File merged_map = bioemma.merged_map
        File all_maps = bioemma.all_maps
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
