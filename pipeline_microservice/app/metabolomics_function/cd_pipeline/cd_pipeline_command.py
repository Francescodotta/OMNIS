import json
import os
import time  # Aggiungi l'import di time
import pandas as pd
from mass_trace import run_mass_trace_detection
from elution_peak import run_elution_peak_detection 
from feature_map import run_feature_mapping
from align_chromatograms import align_featureXML_files
from link_features import link_features
from hmdb_indexing import parse_hmdb_to_dataframe_streaming, search_hmdb_by_mz, consensus_to_feature_dicts, load_kegg_compounds_csv
from batch_correction import normalize_feature_maps
from quality_control import run_qc_advanced  # Aggiungi l'import del modulo QC
from final_report import run_final_report

METABOLOMICS_BASE_PATH = os.getenv("METABOLOMICS_BASE_PATH")

def run_cd_pipeline_from_json(pipeline_json):
    """
    Runs the CD pipeline based on a JSON configuration.
    :param pipeline_json: JSON object describing the pipeline steps and parameters.
    :return: None
    """
    steps = pipeline_json.get("pipeline", {}).get("steps", [])
    mzml_files = []
    results = {}

    # First, select mzML files
    for step in steps:
        if step.get("name") == "select_mzml_file":
            mzml_files = step.get("parameters", {}).get("mzml_files", [])
            break

    if not mzml_files:
        print("No mzML files specified.")
        return

    # Initialize results for each file
    for mzml_file in mzml_files:
        results[mzml_file] = {}

    # Process each step in order
    for step in steps:
        name = step.get("name")
        parameters = step.get("parameters", {})

        for mzml_file in mzml_files:
            if name == "mass_trace_detection":
                # get the parameter 
                polarity = parameters.get("polarity", "negative")
                print(f"Running mass trace detection on {mzml_file} with polarity {polarity}")
                mass_traces = run_mass_trace_detection(mzml_file, polarity=polarity)
                results[mzml_file]["mass_traces"] = mass_traces
            elif name == "elution_peak_detection":
                mass_traces_split = run_elution_peak_detection(results[mzml_file]["mass_traces"])
                results[mzml_file]["elution_peaks"] = mass_traces_split
            elif name == "feature_mapping":
                output_file_fm = run_feature_mapping(mzml_file, results[mzml_file]["elution_peaks"])
                # save the output files which are the mzml list exchanged with the featureXML files
                for i, mzml_file in enumerate(mzml_files):
                    # change the name of mzml into .featureXML
                    results[mzml_file]["output_feature_mapping"] = mzml_file.replace(".mzML", "_feature_map.featureXML")
        
        # alignment
        if name == "align_chromatograms":
            # get the list of featureXML files
            feature_files = [results[mzml_file]["output_feature_mapping"] for mzml_file in mzml_files]
            print(f"Aligning featureXML files: {feature_files}")
            # align the featureXML files
            metrics = align_featureXML_files(feature_files)
            # Qui aggiungi la normalizzazione batch effect
            ref_sample = parameters.get("reference_sample")  # es. "aligned_0.featureXML"
            normalization_method = parameters.get("normalization_method", "tic")  # <--- aggiungi questa riga
            if ref_sample and ref_sample in feature_files:
                ref_index = feature_files.index(ref_sample)
            else:
                ref_index = 0  # default: primo campione
            print(f"Batch correction: reference sample index {ref_index}, method: {normalization_method}")
            normalized_files = normalize_feature_maps(feature_files, reference_index=ref_index, method=normalization_method)
            # Aggiorna i file normalizzati per i passi successivi
            for i, mzml_file in enumerate(mzml_files):
                results[mzml_file]["output_feature_mapping"] = normalized_files[i]
            
        # link features
        if name == "feature_linking":
            # get the list of featureXML files
            feature_files = [results[mzml_file]["output_feature_mapping"] for mzml_file in mzml_files]
            print(f"Linking features in: {feature_files}")
            output_file_consensus = os.path.join(METABOLOMICS_BASE_PATH, "final.consensusXML")
            # link the features
            linked_features = link_features(feature_files, output_file_consensus)
            results[mzml_file]["linked_features"] = linked_features
            # save consensus path in global results for later steps
            results["consensus_file"] = output_file_consensus
            
        # Quality Control Step
        if name == "quality_control":
            # Estrai parametri QC
            qc_name_pattern = parameters.get("qc_name_pattern", "QC")
            save_csv = parameters.get("save_csv", True)
            save_pdf = parameters.get("save_pdf", True)
            save_json = parameters.get("save_json", True)
            run_id = parameters.get("run_id", f"pipeline_{int(time.time())}")
            output_dir = parameters.get("output_dir", os.path.join(METABOLOMICS_BASE_PATH, "qc_results"))
            
            # Prepara i percorsi file
            feature_files = [results[mzml_file]["output_feature_mapping"] for mzml_file in mzml_files]
            
            # Controlla che output_file_consensus esista (creato nel passaggio feature_linking)
            consensus_file = None
            if any(results.get(mzml_file, {}).get("linked_features") for mzml_file in mzml_files):
                consensus_file = os.path.join(METABOLOMICS_BASE_PATH, "final.consensusXML")
            
            print(f"Running quality control analysis (QC pattern: '{qc_name_pattern}')")
            
            # Esegui l'analisi QC
            qc_result = run_qc_advanced(
                mzml_files=mzml_files,
                feature_files=feature_files,
                consensus_file=consensus_file,
                output_dir=output_dir,
                qc_name_pattern=qc_name_pattern,
                save_csv=save_csv,
                save_pdf=save_pdf,
                save_json=save_json,
                run_id=run_id,
                verbose=True
            )
            
            # Memorizza i risultati per ogni file
            for mzml_file in mzml_files:
                results[mzml_file]["qc_report"] = qc_result["report_path"]
                results[mzml_file]["qc_csv"] = qc_result["csv_path"]
            
            # Memorizza anche i risultati globali
            results["qc_global"] = {
                "run_id": qc_result["run_id"],
                "report_path": qc_result["report_path"],
                "csv_path": qc_result["csv_path"],
                "json_path": qc_result["json_path"],
                "plots": qc_result["plots"],
                "runtime_sec": qc_result["runtime_sec"]
            }
            
            print(f"Quality control completed in {qc_result['runtime_sec']} seconds")
            if qc_result.get("qc_metrics"):
                print(f"QC samples found! Mean RSD: {qc_result['qc_metrics']['rsd_mean']:.2f}%")
                print(f"Features with RSD < 30%: {qc_result['qc_metrics']['features_below_30rsd_pct']:.1f}%")

        # Annotazione adotti/isotopi (SPOSTATO PRIMA DEL DATABASE)
        if name == "adduct_isotope_annotation":
            feature_files = [results[mzml_file]["output_feature_mapping"] for mzml_file in mzml_files]
            polarity = parameters.get("polarity", "negative")
            for i, mzml_file in enumerate(mzml_files):
                input_fxml = feature_files[i]
                output_fxml = input_fxml.replace(".featureXML", "_adduct_annotated.featureXML")
                from adduct_isotope_annotation import annotate_adducts_isotopes
                annotate_adducts_isotopes(input_fxml, output_fxml, polarity=polarity)
                results[mzml_file]["output_feature_mapping"] = output_fxml

        # HMDB indexing (ORA DOPO GLI ADDOTTI)
        if name == "hmdb_search":
            print("searching HMDB \n\n\n")
            # get the list of featureXML files
            feature_files = [results[mzml_file]["output_feature_mapping"] for mzml_file in mzml_files]
            print(f"Searching HMDB in: {feature_files}")
            xml_db_path = '/media/datastorage/it_cast/omnis_microservice_db/tools/hmdb_metabolites.xml'
            # parse the HMDB database
            hmdb_df = parse_hmdb_to_dataframe_streaming(xml_db_path)
            kegg_df = load_kegg_compounds_csv('/media/datastorage/it_cast/omnis_microservice_db/tools/kegg_compounds.csv')
            # search the HMDB database
                # convert the consensus to feature dicts
            feature_dicts = consensus_to_feature_dicts(output_file_consensus, hmdb_df, kegg_df, ppm=5)
            print(f"Found {len(feature_dicts)} features in the consensus map.")
            # print the first 5 features
            for i, feat in enumerate(feature_dicts[:5]):
                print(f"Feature {i+1}: m/z={feat['mz']:.5f}, RT={feat['rt']:.2f}")
                print("  HMDB matches:")
                for match in feat["hmdb_matches"]:
                    print(f"    {match}")
                print()
            # save the python df
            df = pd.DataFrame(feature_dicts)
            output_csv_path = os.path.join(METABOLOMICS_BASE_PATH, "hmdb_search_results.csv")
            # remove empty rows in the hmdb_matches column
            df = df[df['hmdb_matches'].apply(lambda x: len(x) > 0)]
            print(f"Found {len(df)} features with HMDB matches.")            # retain the first feature in hmdb_matches
            df['hmdb_matches'] = df['hmdb_matches'].apply(lambda x: x[0] if x else {})
            # save the dataframe to a csv file
            print(f"Saving HMDB search results to {output_csv_path}")
            # retain only the name of the hmdb_matches
            df['hmdb_matches'] = df['hmdb_matches'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
            # remove duplicates in the hmdb_matches column, retain the rows with most input_maps
            df = df.sort_values(by='input_maps', key=lambda x: x.str.len(), ascending=False).drop_duplicates(subset=['hmdb_matches'], keep='first')
            print(df.head())
            df.to_csv(output_csv_path, index=False)
            df.to_excel(output_csv_path.replace('.csv', '.xlsx'), index=False)
            # just retain the first
            # print someone that has the 2 inside the list of input_maps
            results[mzml_file]["hmdb_search_results"] = output_csv_path


        # Final Report Step
        if name == "final_report":
            output_dir = parameters.get("output_dir", os.path.join(METABOLOMICS_BASE_PATH, "final_report"))
            run_id = parameters.get("run_id", f"pipeline_{int(time.time())}")
            
            print("Generating final report")
            
            # Genera il report finale
            final_report_path = run_final_report(results, output_dir, run_id)
            
            # Memorizza il percorso
            results["final_report"] = final_report_path
            
            print(f"Final report completed: {final_report_path}")

    return results

if __name__ == "__main__":
    # load the JSON file
    # Assuming the JSON file is named 'pipeline.json' and is in the same directory
    with open("pipeline.json", "r") as f:
        pipeline_json = json.load(f)
    # Run the CD pipeline
    results = run_cd_pipeline_from_json(pipeline_json)
