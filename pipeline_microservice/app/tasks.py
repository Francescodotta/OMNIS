from app.celery_app import celery_app
from celery import chain
from .metabolomics_function import basic, spectra, compounds, alignment
from app.proteomics_functions import msfragger, percolator, extract_info_flashlfq, flashlfq, uniprot
from app.models.proteomics import ProteomicsPipelineModel
from .pipeline_tasks import flow_cytometry, proteomics
import pyopenms as oms
import redis
import pandas as pd
import os 
from app.models.metabolomics import PipelineModel
from app.metabolomics_function.cd_pipeline.mass_trace import run_mass_trace_detection
from app.metabolomics_function.cd_pipeline.elution_peak import run_elution_peak_detection
from app.metabolomics_function.cd_pipeline.feature_map import run_feature_mapping
from app.metabolomics_function.cd_pipeline.align_chromatograms import align_featureXML_files
from app.metabolomics_function.cd_pipeline.link_features import link_features
from app.metabolomics_function.cd_pipeline.hmdb_indexing import parse_hmdb_to_dataframe_streaming, consensus_to_feature_dicts, load_kegg_compounds_csv
import subprocess
from pyteomics import mztab
import numpy as np
from scipy.stats import ttest_ind


redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

tools_path = os.getenv("TOOLS_BASE_PATH")
METABOLOMICS_BASE_PATH = os.getenv('METABOLOMICS_BASE_PATH')
PROTEOMICS_BASE_PATH = os.getenv('PROTEOMICS_BASE_PATH')


# UTILITIES FUNCTION
def group_annotations_by_id_group(df):
    # Raggruppa i dati basandosi su opt_global_id_group
    grouped = df.groupby('opt_global_id_group').agg({
        'exp_mass_to_charge': 'mean',
        'retention_time': 'mean',
        'description': lambda x: '; '.join(map(str, x.dropna().unique())),  # Convert to string before joining
        'smallmolecule_abundance_study_variable[1]': 'sum',
        'smallmolecule_abundance_study_variable[2]': 'sum',
        'smallmolecule_abundance_study_variable[3]': 'sum',
        
        # Aggiungi altre colonne se necessario
    }).reset_index()

    return grouped


def serialize_ms_experiment(exp):
    """
    Serializza un oggetto MSExperiment in formato JSON, includendo tutti i metadati disponibili
    e aggiungendo un campo per la polarità basato su getPolarity().
    
    Args:
        exp (oms.MSExperiment): Oggetto MSExperiment da serializzare.
    
    Returns:
        str: JSON con dati e metadati degli spettri.
    """
    spectra = exp.getSpectra()

    # Inizializza una lista per i dati degli spettri
    serialized_data = []

    for spectrum in spectra:
        spectrum_data = {
            'RT': spectrum.getRT(),
            'mzarray': list(spectrum.get_peaks()[0]),
            'intarray': list(spectrum.get_peaks()[1]),
            'scan_number': spectrum.getNativeID(),
            'ms_level': spectrum.getMSLevel()
        }

        # Aggiungi tutti i metadati disponibili
        meta_keys = []  # Lista vuota per raccogliere le chiavi
        spectrum.getKeys(meta_keys)  # Popola meta_keys con le chiavi disponibili

        for key in meta_keys:
            try:
                spectrum_data[key] = spectrum.getMetaValue(key)
            except KeyError:
                print(f"Metadata key '{key}' not found in spectrum with RT: {spectrum.getRT()}")

        # Determina la polarità
        polarity_value = spectrum.getInstrumentSettings().getPolarity()
        polarity_map = {0: 'unknown', 1: 'positive', 2: 'negative'}
        spectrum_data['polarity'] = polarity_map.get(polarity_value, 'unknown')

        serialized_data.append(spectrum_data)

    # Crea un DataFrame
    df = pd.DataFrame(serialized_data)

    # Rinominare le colonne con b'' in stringhe normali
    df.rename(columns=lambda x: x.decode('utf-8') if isinstance(x, bytes) else x, inplace=True)

    # Log per verifica
    print(df[['scan_number', 'polarity']].head())

    return df.to_json()


@celery_app.task
def read_mzML_files_task(file_paths:list):
    # lista vuota per leggere i file mzML
    serialized_exp = []
    for file_path in file_paths:
        print(f"Reading file: {file_path}")
        # Implement logic to read mzML files from the given file_path
        metabolomics_exp = basic.read_mzML_file(file_path)
        # fai diventare un df
        serialized_exp.append(serialize_ms_experiment(metabolomics_exp))
    return serialized_exp


@celery_app.task
def select_spectra_task(serialized_experiments, parameters):
    filtered_experiments = []
    for json_exp in serialized_experiments:
        if 'lower_RT' in parameters or 'higher_RT' in parameters:
            lower_RT = parameters.get('lower_RT', None)
            higher_RT = parameters.get('higher_RT', None)
            json_exp = spectra.filter_spectra_RT_time_from_json(json_exp, lower_RT, higher_RT)
        if 'first_scan' in parameters or 'last_scan' in parameters:
            first_scan = parameters.get('first_scan', None)
            last_scan = parameters.get('last_scan', None)
            json_exp = spectra.filter_spectra_scan_from_json(json_exp, first_scan, last_scan)
        if 'scans_to_ignore' in parameters:
            scans_to_ignore = parameters.get('scans_to_ignore', [])
            json_exp = spectra.ignore_scans(json_exp, scans_to_ignore)
        if 'min_peak_count' in parameters:
            min_peak_count = parameters.get('min_peak_count', None)
            json_exp = spectra.filter_min_peak_count_from_json(json_exp, min_peak_count)
        if 'polarity' in parameters:
            polarity = parameters.get('polarity', None)
            print("polarity:", polarity)
            json_exp = spectra.filter_polarity_from_json(json_exp, polarity)
        if 'min_MZ' in parameters or 'max_MZ' in parameters:
            min_MZ = parameters.get('min_MZ', None)
            max_MZ = parameters.get('max_MZ', None)
            json_exp = spectra.filter_MS1_range_from_json(json_exp, min_MZ, max_MZ)
        if 'sn_threshold' in parameters:
            sn_threshold = parameters.get('sn_threshold', None)
            json_exp = spectra.filter_sn_threshold(json_exp, sn_threshold)
        filtered_experiments.append(json_exp)
    return filtered_experiments

# funzione per selezionare lo spettro
@celery_app.task
def select_reference_file_task(parameters):
    # controlla che ci sia un reference nei parametri
    if "reference_file" in parameters:
        reference_file = parameters.get("reference_file")
        return reference_file


@celery_app.task
def align_spectra_task(serialized_experiments, parameters):
    # controlla che ci sia un reference file nei parametri
    if "reference_file" in parameters:
        # leggi il file e trasformalo in json
        reference_file = parameters.get("reference_file")
        reference_exp = basic.read_mzML_file(reference_file)
        serialized_exp = serialize_ms_experiment(reference_exp)
        # pipeline di allineamento
        aligned_exp = alignment.align_chromatograms(serialized_exp, serialized_experiments)
        return aligned_exp
    else:
        pass

@celery_app.task
def detect_compounds_task(serialized_experiments, parameters):
    print("parameters:", parameters)    
    for json_exp in serialized_experiments:
        if "mass_tolerance_ppm" in parameters:
            mass_tolerance_ppm = parameters.get("mass_tolerance_ppm")
            chromatograms = compounds.extract_chromatograms_from_json(json_exp, mass_tolerance_ppm)
        if "min_peak_intensity" in parameters:
            min_peak_intensity = parameters.get("min_peak_intensity")
            chromatograms = compounds.filter_peaks_by_intensity(chromatograms, min_peak_intensity)
        if "min_scans_per_peak" in parameters:
            min_scans_per_peak = parameters.get("min_scans_per_peak")
            chromatograms = compounds.filter_chromatograms_by_scans(chromatograms, min_scans_per_peak)
        if "most_intense_isotope_only" in parameters:
            most_intense_isotope_only = parameters.get("most_intense_isotope_only")
            chromatograms = compounds.process_isotopes_from_json(chromatograms, most_intense_isotope_only)
        if "max_gaps" in parameters:
            max_gaps = parameters.get("max_gaps")
            chromatograms = compounds.correct_gaps_from_json(chromatograms, max_gaps)
        if "min_adjacent_non_zeros" in parameters and "max_gaps_max" in parameters:
            min_adjacent_non_zeros = parameters.get("min_adjacent_non_zeros")
            max_gaps_max = parameters.get("max_gaps_max")
            chromatograms = compounds.correct_gaps_with_min_adjacent_non_zeros(chromatograms, max_gaps_max, min_adjacent_non_zeros)
        if "sn_threshold" in parameters:
            sn_threshold = parameters.get("sn_threshold")
            chromatograms = compounds.signal_noise_threshold_detectCompounds(chromatograms, sn_threshold)
        if "remove_baseline" in parameters:
            remove_baseline = parameters.get("remove_baseline")
            if remove_baseline:
                chromatograms = compounds.remove_baseline(chromatograms)
        if "gap_ratio_threshold" in parameters:
            gap_ratio_threshold = parameters.get("gap_ratio_threshold")
            chromatograms = compounds.filter_chromatograms_by_gap_ratio(chromatograms, gap_ratio_threshold)
        if "max_peak_width" in parameters:
            max_peak_width = parameters.get("max_peak_width")
            chromatograms = compounds.filter_by_max_peak_width(chromatograms, max_peak_width)
        if "min_valley_depth" in parameters:
            min_valley_depth = parameters.get("min_valley_depth")
            chromatograms = compounds.filter_peaks_by_min_relative_valley_depth(chromatograms, min_valley_depth)
        if "additional_elements" in parameters:
            additional_elements = parameters.get("additional_elements")
            chromatograms = compounds.group_isotopes(chromatograms, additional_elements)
        else:
            pass
    return chromatograms
    
@celery_app.task
def group_compounds_task(chromatograms_json, parameters):
    """
    Task to group compounds from the chromatograms using specified parameters.

    Parameters:
    - chromatograms_json (str): JSON string representing the chromatograms.
    - parameters (dict): Dictionary containing parameters for grouping compounds.

    Returns:
    - str: JSON string of grouped compounds.
    """
    # Extract parameters with default values
    rt_tolerance = parameters.get('rt_tolerance', 0.8)
    mass_tolerance_ppm = parameters.get('mass_tolerance_ppm', 10)
    use_isotope_pattern = parameters.get('use_isotope_pattern', True)

    # Call the group_compounds function from the compounds module
    grouped_compounds_json = compounds.group_compounds(
        filtered_results_json=chromatograms_json,
        rt_tolerance=rt_tolerance,
        mass_tolerance_ppm=mass_tolerance_ppm,
        use_isotope_pattern=use_isotope_pattern
    )

    return grouped_compounds_json
    
    

def create_pipeline_chain(data):
    """
    Crea ed esegue una catena di task Celery basata sui dati della pipeline.
    
    Args:
        data (dict): Configurazione della pipeline.
    
    Returns:
        AsyncResult: Risultato asincrono della catena.
    """
    steps = data.get('pipeline', {}).get('steps', [])
    if not steps:
        raise ValueError("Pipeline steps not defined in the data.")

    task_chain = []

    for step in steps:
        name = step.get('name')
        parameters = step.get('parameters', {})
        print("name:", name)    
        if name == 'select_mzML_files':
            file_paths = parameters.get('file_paths', [])
            task_chain.append(read_mzML_files_task.s(file_paths))

        elif name == 'select_spectra':
            task_chain.append(select_spectra_task.s(parameters))

        elif name == 'align_spectra':
            task_chain.append(align_spectra_task.s(parameters))

        elif name == 'detect_compounds':
            task_chain.append(detect_compounds_task.s(parameters))
        elif name == 'group_compounds':
            task_chain.append(group_compounds_task.s(parameters))
        else:
            raise ValueError(f"Unknown step: {name}")

    # Costruire la catena
    return chain(*task_chain)


# Create a pipeline chain for flow cytometry analysis
def create_flow_cytometry_pipeline_chain(data):
    """
    Create a Celery chain of tasks for flow cytometry analysis.

    Args:
        data (dict): The pipeline configuration data.

    Returns:
        chain: A Celery chain object for executing the tasks.
    """
    # get the name of the pipeline
    name = data.get('name')
    print("name:", name)
    
    steps = data.get('pipeline', {}).get('steps', [])
    print("\n\n\n\n")
    print("steps:", steps)
    task_chain = []
    if not steps:
        raise ValueError("Pipeline steps not defined in the data.")

    for step in steps:
        print("step:", step)
        name = step.get('name')
        parameters = step.get('parameters', {})

        if name == 'select_fcs_files':
            print("functioning")
            file_paths = parameters.get('file_paths', [])
            task_chain.append(flow_cytometry.select_fcs_files_task.s(file_paths))

        if name == 'umap':
            # UMAP step outputs both reduced and original data
            task_chain.append(flow_cytometry.umap_dimensionality_reduction_task.s(parameters))

        if name == 'louvain_clustering':
            # Louvain clustering (assuming it uses UMAP-reduced data)
            task_chain.append(flow_cytometry.louvain_clustering_task.s(parameters))

        if name == 'leiden_clustering':
            # Leiden clustering now expects the full UMAP result
            print("Adding Leiden clustering task to the chain. \n\n", parameters)
            task_chain.append(flow_cytometry.leiden_clustering_task.s(parameters))
        
        if name == "generate_heatmap_data":
            print("Adding generate_heatmap_data_task to the chain. \n\n", parameters)
            task_chain.append(flow_cytometry.generate_heatmap_data_task.s(parameters))
        
        if name == "flowsom_clustering":
            # Extract the flowsom parameters
            flowsom_parameters = parameters.get('flowsom_parameters', {})
            parameters.update(flowsom_parameters)

            # Extract required arguments
            json_str = parameters.get('json_str', '')
            n_clusters = int(parameters.get('n_clusters', 10))
            xdim = int(parameters.get('xdim', 10))
            ydim = int(parameters.get('ydim', 10))

            print("Adding flowsom_clustering_task to the chain. \n\n", parameters)

            # Add the task to the chain with keyword arguments
            task_chain.append(
                flow_cytometry.flowsom_clustering_task.s(
                    n_clusters=n_clusters,
                    xdim=xdim,
                    ydim=ydim
                )
            )
        
        if name == "plot_scatter":
            task_chain.append(flow_cytometry.plot_scatter_task.s(parameters))    
                     
        if name == 'plot_matrix':
            task_chain.append(flow_cytometry.plot_matrix_task.s(parameters))

    return chain(*task_chain)


# create a pipeline chain for proteomics analysis
def create_proteomics_pipeline_chain(data):
    """
    Crea ed esegue una catena di task Celery basata sui dati della pipeline.
    
    Args:
        data (dict): Configurazione della pipeline.
    
    Returns:
        AsyncResult: Risultato asincrono della catena.
    """
    steps = data.get('pipeline', {}).get('steps', [])
    if not steps:
        raise ValueError("Pipeline steps not defined in the data.")

    task_chain = []

    for step in steps:
        name = step.get('name')
        parameters = step.get('parameters', {})
        print("name:", name)
        if name == 'select_mzML_files':
            file_paths = parameters.get('file_paths', [])
            task_chain.append(proteomics.select_mzml_files.s(file_paths))
        elif name == 'select_spectra':
            task_chain.append(proteomics.select_spectra.s(parameters))
        elif name == 'msfragger':
            # MSFragger step outputs both reduced and original data
            task_chain.append(proteomics.msfragger_step.s(parameters))


        else:
            raise ValueError(f"Unknown step: {name}")

    # Costruire la catena
    return chain(*task_chain)   


@celery_app.task(bind=True) 
def metabolomics_workflow(self, data):
    """
    This function allows the execution of the untargeted LC-MS metabolomics pipeline. 
    """

    # define the task id
    task_id = self.request.id
    # ADD LOGGING STATEMENT REFERRING TO THE TASK ID
    # DEFINE THE RESULTS DIRECTORY
    results_dir = os.path.join(METABOLOMICS_BASE_PATH, task_id)
    if task_id not in os.listdir(METABOLOMICS_BASE_PATH):
        os.makedirs(results_dir)
    # get all the steps of the pipeline
    steps = data.get('pipeline', {}).get('steps', [])
    # initialize empty dict for results and empty list for the paths of the file selected for the analysis
    results = {}
    file_paths = []

    # check if the steps are present in the pipeline, otherwise return an error
    if not steps:
        # ADD A LOG ERROR STATEMENT 
        raise ValueError('Pipeline steps are not defined in the data, impossible to process')

    for step in steps:
        if step.get('name') == "select_mzML_files":
            file_paths = step.get('parameters', {}).get('file_paths', [])
            if not file_paths:
                raise ValueError('The pipeline cannot run without mzml files')
            print(f'found {len(file_paths)} in the data')
            break
    if not file_paths:
        raise ValueError('No select mzML file found in the pipeline')
    

    for step_idx, step in enumerate(steps):
        name = step.get('name')
        parameters = step.get('parameters')

        if name == "FeatureFinder":
            feature_files = []
            for file_path in file_paths:
                base_name = os.path.basename(file_path).replace(".mzML", "")
                feature_file = os.path.join(results_dir, f"{base_name}.featureXML")
                feature_files.append(feature_file)
                cmd = [
                    "FeatureFinderMetabo", "-in", file_path, "-out", feature_file
                ]
                try:
                    subprocess.run(cmd, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error in processing the {file_path} file: {e}")
        elif name.lower() == "aligner":
            aligned_files = [os.path.join(results_dir, f"aligned_{os.path.basename(file_path).replace(".mzML","")}.featureXML") for file_path in file_paths]

            cmd = ["MapAlignerPoseClustering", "-in", *feature_files, "-out", *aligned_files]
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error during map alignment: {e}")
        elif name.lower() == "LinkingQT":
            output_consensus = os.path.join(results_dir, "consensus_file.consensusXML")
            cmd = ["FeatureLinkerUnlabeledQT", "-in", *aligned_files, "-out", output_consensus]
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error during the feature linking step: {e}")    
        elif name.lower() == "ms1_annotation":
            cmd = ["AccurateMassSearch", "-in", output_consensus, "-out", os.path.join(results_dir, "annotated_consensus.mzTab")]
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error during the mass accurate search step: {e}")
        elif name.lower() == "sirius_annotation":
            sirius_output_dir = os.path.join(results_dir, "sirius_output")
            if not os.path.exists(sirius_output_dir):
                os.makedirs(sirius_output_dir)
            for file_path in file_paths:
                base_name = os.path.basename(file_path).replace(".mzML", "")
                sirius_output_file_mztab = os.path.join(sirius_output_dir, f"{base_name}_sirius.mzTab")
                sirius_cmd = [
                    "SiriusAdapter", "-in", file_path, "-out_sirius", sirius_output_file_mztab 
                ]
                try:
                    subprocess.run(sirius_cmd, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error during SIRIUS annotation for file {file_path}: {e}")
        elif name.lower() == "mztab_processing":
            mztab_file = os.path.join(results_dir, "annotated_consensus.mzTab")
            # implement the mzTab processing function here
            tab_data = mztab.MzTab(mztab_file)  
            try:
                # Tabella dei metaboliti (quella che ti serve per metabolomica)
                metabolites_df = pd.DataFrame(tab_data.small_molecule_table)
            except AttributeError:
                print("No small molecule table found")
            grouped_df = group_annotations_by_id_group(metabolites_df)
            output_csv = os.path.join(results_dir, "grouped_metabolites_annotations.csv")
            grouped_df.to_csv(output_csv, index=False)
        elif name.lower() == "MS2_Annotation":
            # implement the MS2 annotation step here
            pass
        elif name.lower() == "statistics":
            # take a mtx file as input with labels 
            fc_threshold = 1
            p_value_threshold = 0.05
            
            pass
        # address the results from the mztab!!

            
        



# If you want to setup the PyOpenMS module instead of the OpenMS
@celery_app.task(bind=True)
def run_metabolomics_pipeline_task(self, data):
    """ 
    Esegue la pipeline di proteomica attraverso i dati forniti tramite un file JSON che serve a costruire la pipeline utilizzando i parametri personalizzati dall'utente
    
    Args:
        data(dict): Configurazione della pipeline di metabolomica.
        
    Returns:
        AsyncResult: Risultato ottenuto in modo asincrono dalla catena di task
    
    """
    task_id = self.request.id
    print(f"Running metabolomics pipeline with task ID: {task_id}")
    
    steps = data.get('pipeline', {}).get('steps', [])
    results = {}
    file_paths = []
    output_file_consensus = None
    
    if not steps:
        raise ValueError('Pipeline steps are not defined in the data')
    
    for step in steps:
        if step.get('name') == "select_mzML_files":
            file_paths = step.get('parameters', {}).get('file_paths', [])
            if not file_paths:
                raise ValueError('The pipeline cannot run without mzml files')
            print(f'found {len(file_paths)} in the data')
            break
    if not file_paths:
        raise ValueError('No select mzML file found in the pipeline')
    
    # initialize result 
    for file_path in file_paths:
        results[file_path] = {}
        print(f'Initialized {os.path.basename(file_path)}')
        
    print('Executing Pipeline steps')
    
    for step_idx, step in enumerate(steps):
        name = step.get('name', None)
        parameters = step.get('parameters', {})
        
        if name == 'select_mzML_files':
            print('files already loaded')
            continue
        
        elif name == 'mass_trace_detection':
            polarity = parameters.get('polarity', 'negative')
            print('Running mass traces polarity')
            for i, file_path in enumerate(file_paths):
                try:
                    mass_traces = run_mass_trace_detection(file_path, polarity=polarity)   
                    results[file_path]['mass_traces'] = mass_traces
                except Exception as e:
                    print(f'Mass trace detection failed due to the following error: \n {e}')
                    raise e
        
        elif name == 'elution_peak_detection':
            print('Running elution peak detection')
            for i, file_path in enumerate(file_paths):
                if 'mass_traces' not in results[file_path]:
                    raise ValueError(f'mass_traces not found for the {file_path}, Run mass trace step before elution peak')
                try:
                    mass_traces_split = run_elution_peak_detection(results[file_path]['mass_traces'])
                    results[file_path]['elution_peaks'] = mass_traces_split
                except Exception as e:
                    print('Elution peak detection failed due to the following error: \n {e}')
                    raise e
            
        elif name == 'feature_mapping':
            print('Running feature mapping step')
            for i, file_path in enumerate(file_paths):
                if 'elution_peaks' not in results[file_path]:
                    raise ValueError(f'Elution peak not found for the {file_path}, please run first the elution peak detection step for this sample')
                try:
                    run_feature_mapping(file_path, results[file_path]['elution_peaks'])
                    output_path = file_path.replace('.mzML', '_feature_map.featureXML')
                    results[file_path]['output_feature_mapping'] = output_path
                    print(f'Feature mapping for the {file_path} file completed')
                    
                except Exception as e:
                    print(f'Feature mapping failed due to the following error \n {e}')
                    raise e
                
        elif name == 'align_chromatograms':
            print("📊 Running chromatogram alignment")
            
            # collect feature files
            feature_files = []
            for file_path in file_paths:
                if 'output_feature_mapping' not in results[file_path]:
                    raise ValueError(f'output_feature_mapping not found for {file_path}')
                feature_files.append(results[file_path]['output_feature_mapping'])
                
            try:
                metrics = align_featureXML_files(feature_files)
            except Exception as e:
                print(f'The alignment process ended with the following error: \n {e}')
        
        elif name == 'feature_linking':
            print('Running feature linking step')
            try:
                output_file_consensus = os.path.join(METABOLOMICS_BASE_PATH, 'final.consensusXML')
                linked_features = link_features(feature_files, output_file_consensus)
                # store consensus results globally and not per file since it's merged data
                results['_consensus'] = {
                    'consensus_file': output_file_consensus, 
                    'linked_features': linked_features
                }
            except Exception as e:
                print(f'The feature linking step ended due to the following error: {e}')
        
        elif name == 'hmdb_search':
            print('running hmdb search')
            
            # check if consensus file exists
            if not output_file_consensus or '_consensus' not in results:
                raise ValueError('Consensus file not found, run feature_linking first')
            
            try:
                xml_db_path = os.path.join(tools_path, 'hmdb_metabolites.xml')
                if not os.path.exists(xml_db_path):
                    raise FileNotFoundError(f'HMDB Database not found: {xml_db_path}')
                
                kegg_db_path = os.path.join(tools_path, 'kegg_compounds.csv')
                if not os.path.exists(kegg_db_path):
                    raise FileNotFoundError(f'KEGG Database not found: {kegg_db_path}')
                kegg_df = load_kegg_compounds_csv(kegg_db_path)

                print('Loading hmdb database... \n')
                hmdb_df = parse_hmdb_to_dataframe_streaming(xml_db_path)
                
                print('searching features against HMDB.. \n')
                feature_dicts = consensus_to_feature_dicts(output_file_consensus, hmdb_df, kegg_df)
                print(f'Found {len(feature_dicts)} in the consensus map')
                
                if feature_dicts:
                    df = pd.DataFrame(feature_dicts)
                    initial_count = len(df)
                    # filter and process results
                    df = df[df['hmdb_matches'].apply(lambda x: len(x) > 0)]
                    filtered_count = len(df)
                    
                    if filtered_count > 0:     
                        df = df.sort_values(
                            by='input_maps',
                            key=lambda x: x.str.len(),
                            ascending = False
                        ).drop_duplicates(subset=['hmdb_matches'], keep = 'first')
                        output_csv_path = os.path.join(METABOLOMICS_BASE_PATH, 'hmdb_search_results_pipeline.csv')
                        df.to_csv(output_csv_path)
                        results['_consensus']['hmdb_search_results'] = output_csv_path
                        # save the csv into the metabolomics database 
                        PipelineModel.update_by_task_id(task_id,  {'hmdb_search_result':output_csv_path})
                        PipelineModel.update_status_by_task_id(task_id, 'completed')
                        print('HMDB search completed')
                    else:
                        print('No HMDB matches found')
                else:
                    print('No features found in consensus map')
                
            except Exception as e:
                print('HMDB search failed')
                raise e
            
        else:
            print(f'Unknown step name - {name} - SKIPPING \n')
            
    print('\n PIPELINE COMPLETED SUCCESFULLY')
    return output_csv_path


