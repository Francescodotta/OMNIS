from app.celery_app import celery_app
from celery import chain
import redis
import pandas as pd
import os 
from app.models.metabolomics import PipelineModel, MetabolomicsMatrixModel
from app.metabolomics_function.statistics.processed_data import read_processed_matrix, calculate_statistics, generate_volcano_data, save_volcano_plot
import subprocess
from pyteomics import mztab
from app.models.flow_cytometry import FlowCytoPipelineRun, FlowCytometryModel
from app.flow_cytometry_functions.processing import umap
from app.flow_cytometry_functions.statistics import data_loading, preprocessing, pairwise_analysis, visualization
from app.flow_cytometry_functions.utilities import loading

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

tools_path = os.getenv("TOOLS_BASE_PATH")
METABOLOMICS_BASE_PATH = os.getenv('METABOLOMICS_BASE_PATH')
FLOW_CYTOMETRY_BASE_PATH = os.getenv('FLOW_CYTOMETRY_BASE_PATH')





@celery_app.task(bind=True)
def flow_cytometry_unserialized(self, data) -> dict:
    """
    Function to run the flow cytometry pipeline without serialization and taskification.
    
    Args:
        data (dict): Pipeline configuration data.
        
    Returns:
        dict: Results of the flow cytometry analysis. 
    """
    # Get the name of the pipeline
    name = data.get('name')
    print("Pipeline name:", name)
    task_id = self.request.id

    # Initialize pipeline status
    pipeline_status = "initiated"
    FlowCytoPipelineRun.update_by_chain_id(task_id, {'status': pipeline_status})

    # Get the steps of the pipeline
    steps = data.get('pipeline', {}).get('steps', [])
    if not steps:
        raise ValueError("Pipeline steps not defined in the data.")

    # Initialize step statuses
    step_statuses = {step.get('name'): "waiting" for step in steps}
    FlowCytoPipelineRun.update_by_chain_id(task_id, {'step_statuses': step_statuses})

    # Initialize results
    results = {}
    results_dir = os.path.join(FLOW_CYTOMETRY_BASE_PATH, task_id)
    if task_id not in os.listdir(FLOW_CYTOMETRY_BASE_PATH):
        os.makedirs(results_dir)
    # Update pipeline status to "in progress"
    pipeline_status = "in progress"
    FlowCytoPipelineRun.update_by_chain_id(task_id, {'status': pipeline_status})

    try:
        for step in steps:
            step_name = step.get('name')
            parameters = step.get('parameters', {})

            # Update the current step to "in progress"
            step_statuses[step_name] = "in progress"
            FlowCytoPipelineRun.update_by_chain_id(task_id, {'step_statuses': step_statuses})

            try:
                if step_name == 'select_fcs_files':
                    print("Processing step: select_fcs_files")
                    files_info = parameters.get('files_info', [])
                    progressive_ids = [f['file_id'] for f in files_info]
                    file_paths = [f['file_path'] for f in files_info]
                    filenames = [f['filename'] for f in files_info]
                    metadata_list = [f['metadata'] for f in files_info]
                    
                    # 🦍 FIX: Raccogli tutte le chiavi presenti in almeno un file
                    all_keys = set()
                    for meta in metadata_list:
                        all_keys.update(meta.keys())
                    
                    # Escludi chiavi non rilevanti
                    excluded_keys = {'user_id', 'workspace', 'workspace_id', 'created_at', 'updated_at', '_id'}
                    all_keys = all_keys - excluded_keys
                    
                    combined_metadata = {}
                    for key in all_keys:
                        # 🦍 FIX: Usa .get() con default None per chiavi mancanti
                        combined_metadata[key] = [meta.get(key, None) for meta in metadata_list]

                    # get the name of the combined metadata columns
                    metadata_list = combined_metadata.keys()
                    print("Combined metadata columns:", metadata_list)
                    df_fcs = loading.load_fcs_files(file_paths, progressive_ids, filenames, combined_metadata)

                elif step_name == 'umap':
                    print("Processing step: umap")
                    print(df_fcs.head())
                    # get the parameters for umap
                    if isinstance(parameters, dict):
                        umap_params = parameters.get('umap') or {}
                        # fallback: se i parametri sono direttamente nella dict (es. {'n_neighbors':..., 'min_dist':...})
                        if not umap_params:
                            for k in ('n_neighbors', 'min_dist'):
                                if k in parameters:
                                    umap_params[k] = parameters[k]
                    n_neighbors = umap_params.get('n_neighbors', 15)
                    min_dist = umap_params.get('min_dist', 0.1)
                    adata = umap.umap_dimensionality_reduction(df_fcs, metadata_columns=metadata_list, n_neighbors=int(n_neighbors), min_dist=float(min_dist))
                    del df_fcs
                    df = adata.to_df()
                    df['file_id'] = adata.obs['file_id'].values
                    df['filename'] = adata.obs['filename'].values
                    df['UMAP1'] = adata.obsm['X_umap'][:, 0]
                    df['UMAP2'] = adata.obsm['X_umap'][:, 1]
                    # insert metadata into df
                    for col in adata.obs.columns:
                        print(adata.obs.columns)
                        if col not in ['file_id', 'filename']:
                            df[col] = adata.obs[col].values
                    umap_results_path = os.path.join(FLOW_CYTOMETRY_BASE_PATH, task_id, 'umap_results.csv')
                    os.makedirs(os.path.dirname(umap_results_path), exist_ok=True)
                    df.to_csv(umap_results_path, sep='\t', index=False)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'umap_results_path': umap_results_path})

                elif step_name == 'unsupervised_clustering':
                    # the umap step must be run before
                    if 'umap_results_path' not in FlowCytoPipelineRun.find_by_chain_id(task_id):
                        raise ValueError("UMAP results not found. Please run UMAP step before unsupervised clustering.")
                    print("Processing step: unsupervised_clustering")
                    adata = umap.clustering(adata, method='leiden', **parameters)
                    # extract leiden cluster
                    df['Leiden_cluster'] = adata.obs['leiden'].values
                    # same csv
                    df.to_csv(umap_results_path, sep='\t', index=False)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'umap_results_path': umap_results_path})

                elif step_name == "flowsom_clustering":
                    print("Processing step: flowsom_clustering")
                    adata = umap.flowsom_clustering(adata, **parameters)
                    # take the flowsom cluster into csv
                    df['Flowsom_cluster'] = adata.obs['flowsom_cluster'].values
                    # same csv
                    df.to_csv(umap_results_path, sep='\t', index=False)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'umap_results_path': umap_results_path})

                elif step_name == "plot_scatter":
                    print("Processing step: plot_scatter")
                    scatter_plot_path = visualization.plot_scatter(adata, **parameters)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'scatter_plot_path': scatter_plot_path})

                elif step_name == "plot_matrix":
                    print("Processing step: plot_matrix")
                    matrix_plot_path = visualization.plot_matrix(adata, **parameters)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'matrix_plot_path': matrix_plot_path})
                
                elif step_name == "select_fcs_file_pairwise_analysis":
                    progressive_id_list = parameters.get('files', [])
                    pairs = data_loading.load_control_treatment_maps(progressive_id_list)
                    print("pairs:", pairs)
                
                elif step_name == "pairwise_preprocessing_analysis":
                    annotated_df = parameters.get('files', [])
                    pairs = data_loading.load_control_treatment_maps(progressive_id_list)
                    mean_df = preprocessing.extract_raw_means(annotated_df)
                    scaled_means_df = preprocessing.apply_standard_scaling(mean_df)

                elif step_name == "outlier_removal":
                    cleaned_df = preprocessing.remove_outliers_iqr(scaled_means_df)

                elif step_name == "pairwise_analysis":
                    pairwise_results = pairwise_analysis.compute_pairwise_differences(cleaned_df, pairs)
                    marker_columns = [col for col in pairwise_results.columns if col not in ['treatment_id', 'control_id']]
                    metrics_df = pairwise_analysis.compute_statistical_metrics(pairwise_results, marker_columns)
                    heatmap_df = pairwise_results.set_index('treatment_id')
                    heatmap_df = heatmap_df.drop(columns=['control_id'], errors='ignore')
                    # path for heatmap csv
                    heatmap_difference_path_csv = os.path.join(results_dir, "heatmap_differences.csv")
                    # path for metrics csv
                    metrics_path_csv = os.path.join(results_dir, "pairwise_metrics.csv")
                    # save metrics csv
                    metrics_df.to_csv(metrics_path_csv)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'pairwise_metrics_path_csv': metrics_path_csv})
                    # save heatmap csv
                    heatmap_df.to_csv(heatmap_difference_path_csv)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'heatmap_difference_path_csv': heatmap_difference_path_csv})
                elif step_name == "visualization_plots":
                    heatmap_difference_path = visualization.heatmap_differences_visualization(heatmap_df)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'heatmap_difference_path': heatmap_difference_path})
                    heatmap_consistent_parameters_path = visualization.heatmap_consistent_parameters(heatmap_df)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'heatmap_consistent_parameters_path': heatmap_consistent_parameters_path})
                    barplot_effect = visualization.barplot_cohen_effect_size_horizontal(metrics_df)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'barplot_effect': barplot_effect})
                    volcano_plot_path = visualization.volcano_plot_exploratory(metrics_df)
                    FlowCytoPipelineRun.update_by_chain_id(task_id, {'volcano_plot_path': volcano_plot_path})


                else:
                    print(f"Unknown step: {step_name} - skipping")
                    continue

                # Update the current step to "completed"
                step_statuses[step_name] = "completed"
                FlowCytoPipelineRun.update_by_chain_id(task_id, {'step_statuses': step_statuses})

            except Exception as e:
                # Update the current step to "failed"
                step_statuses[step_name] = "failed"
                FlowCytoPipelineRun.update_by_chain_id(task_id, {'step_statuses': step_statuses})
                raise Exception(f"Error in step '{step_name}': {str(e)}")

        # Update pipeline status to "completed"
        pipeline_status = "completed"
        FlowCytoPipelineRun.update_by_chain_id(task_id, {'status': pipeline_status})

        print("Pipeline completed successfully")
        return results

    except Exception as e:
        # Update pipeline status to "failed"
        pipeline_status = "failed"
        FlowCytoPipelineRun.update_by_chain_id(task_id, {
            'status': pipeline_status,
            'error_message': str(e)
        })
        print(f"Pipeline failed: {str(e)}")
        raise e


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
    # output path directory
    results_dir = os.path.join(METABOLOMICS_BASE_PATH, task_id)
    if task_id not in os.listdir(METABOLOMICS_BASE_PATH):
        os.makedirs(results_dir)

    if not steps:
        raise ValueError('Pipeline steps are not defined in the data')
    
    for step in steps:
        print(step)
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
        name = step.get('name')
        parameters = step.get('parameters')
        
        if name == 'select_mzML_files':
            print('files already loaded')
            continue

        if name.lower() == 'featurefinder':
            feature_files = []
            for file_path in file_paths:
                base_name = os.path.basename(file_path).replace(".mzML", "")
                feature_file = os.path.join(results_dir, f"{base_name}.featureXML")
                feature_files.append(feature_file)
                ## DEFINE THE INI --- AT THE MOMENT DEFAULT 

                cmd = [
                    "FeatureFinderMetabo", "-in", file_path, "-out", feature_file
                ]
                try:
                    subprocess.run(cmd, check=True)
                    print(f'Feature finding completed for {file_path}')
                except subprocess.CalledProcessError as e:
                    print(f"Error in processing the {file_path} file: {e}")

        elif name.lower() == "aligner":
            aligned_files = [os.path.join(results_dir, f"aligned_{os.path.basename(file_path).replace('.mzML','')}.featureXML") for file_path in file_paths]

            cmd = ["MapAlignerPoseClustering", "-in", *feature_files, "-out", *aligned_files]
            try:
                subprocess.run(cmd, check=True)
                print('Map alignment completed')
            except subprocess.CalledProcessError as e:
                print(f"Error during map alignment: {e}")
    
        elif name.lower() == "linkingqt":
            output_consensus = os.path.join(results_dir, "consensus_file.consensusXML")
            cmd = ["FeatureLinkerUnlabeledQT", "-in", *aligned_files, "-out", output_consensus]
            try:
                subprocess.run(cmd, check=True)
                print('Feature linking completed')
            except subprocess.CalledProcessError as e:
                print(f"Error during the feature linking step: {e}")

        elif name.lower() == "ms1_annotation":
            annotated_mztab = os.path.join(results_dir, "annotated_consensus.mzTab")
            cmd = ["AccurateMassSearch", "-in", output_consensus, "-out", annotated_mztab]
            try:
                subprocess.run(cmd, check=True)
                print('Mass accurate search completed')
                results['annotated_mztab'] = annotated_mztab
            except subprocess.CalledProcessError as e:
                print(f"Error during the mass accurate search step: {e}")
        
        # process annotated mztab to extract matrix
        elif name.lower() == "extract_matrix":
            print('Extracting matrix from annotated mztab')
            try:
                tab_data = mztab.MzTab(annotated_mztab)

                matrix_df = pd.DataFrame(tab_data.small_molecule_table)
                matrix_path = os.path.join(results_dir, 'metabolomics_matrix.csv')

            except Exception as e:
                print(f'Error extracting matrix from mztab: {e}')
                raise e



        elif name == 'select_raw_matrix':
            # progressive id from parameters
            progressive_id = parameters.get('progressive_id', None)
            if not progressive_id:
                raise ValueError('progressive_id not found in parameters')
            print(f'Loading matrix data for progressive id: {progressive_id}')
            try:
                # now progressive id is a list --- take the first element
                progressive_id = progressive_id[0] if isinstance(progressive_id, list) else progressive_id
                metabo_matrix = MetabolomicsMatrixModel.find_by_progressive_id(int(progressive_id))
                matrix_path = metabo_matrix['matrix_file']
                group1, group2 = read_processed_matrix(matrix_path)
                print(group1.columns)
            except Exception as e:
                print(f'Error loading matrix data: {e}')
                raise e
        elif name == 'metabolomics_statistical_analysis':
            print('Calculating statistics on the loaded matrix data')
            try:
                stats_results = calculate_statistics(group1, group2)
                volcano_df = generate_volcano_data(stats_results)
                output_volcano_path = os.path.join(results_dir, 'volcano_data.csv')
                volcano_df.to_csv(output_volcano_path, index=False)
                results['csv_volcano_data'] = output_volcano_path
            except Exception as e:
                print(f'Error calculating statistics: {e}')
                raise e
        elif name == "metabolomics_volcano_plot":
            try:
                volcano_plot_path = os.path.join(results_dir, 'volcano_plot.png')
                save_volcano_plot(volcano_df, volcano_plot_path)
                results['final_volcano_plot'] = volcano_plot_path
            except Exception as e:
                print(f'Error generating volcano plot: {e}')
                raise e


        else:
            print(f'Unknown step name - {name} - SKIPPING \n')
            
    print('\n PIPELINE COMPLETED SUCCESFULLY')
    print('Results dictionary keys:', results.keys())
    # save the results into the database
    PipelineModel.update_by_task_id(task_id, {'results': results})
    PipelineModel.update_status_by_task_id(task_id, 'completed')
    return results
