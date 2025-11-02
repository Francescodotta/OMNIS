from app.helpers import metabolomics_helpers
from app.models.metabolomics_models import MetabolomicsModel, PipelineModel
from app.utils import metabolomics, security, pipeline
import hashlib
import json
import pandas as pd
import ast 
from dotenv import load_dotenv
import os

load_dotenv()

METABOLOMICS_SECRET_KEY = os.getenv('METABOLOMICS_SECRET_KEY')

def upload_metabolomics_experiment_views(user_id, project_id, experimentName, metabolomics_file):
    # controlla che l'utente sia registrato e che il progetto esista
    response, status = metabolomics_helpers.validate_metabolomics_data(user_id, project_id, experimentName, metabolomics_file)
    if status != 200:
        return response, status
    # salva il file
    response, status = metabolomics_helpers.save_file(metabolomics_file)
    if status != 200:
        return response, status
    # crea un nuovo esperimento di metabolomica
    metabolomics_mzML_path = metabolomics.convert_raw_to_mzml(response)
    # hash del nome dell'esperimento
    experiment_name_hash = hashlib.sha256(experimentName.encode()).hexdigest()
    metabolomics_data = {"project_id": project_id, 
                         "metabolomics_experiment_name": experimentName, 
                         "metabolomics_experiment_file": response, 
                         "metabolomics_mzML_file": metabolomics_mzML_path, 
                         "experiment_name_hash": experiment_name_hash}
    # cripta i dati di metabolomica
    for key, value in metabolomics_data.items(): 
        if key != "project_id" and key != "experiment_name_hash":
            metabolomics_data[key] = security.encrypt_data(str(value))
    MetabolomicsModel.create_metabolomics_data(metabolomics_data)
    return {"message": "Metabolomics experiment uploaded correctly"}, 201


# funzione per leggere un esperimento di metabolomica
def get_metabolomics_experiment_views(metabolomics_id):
    metabolomics_data = MetabolomicsModel.find_by_progressive_id(metabolomics_id)
    metabolomics_data.pop("_id")
    if not metabolomics_data:
        return {"error": "Metabolomics experiment not found"}, 404
    # decripta i dati di metabolomica
    for key, value in metabolomics_data.items():
        if key != "project_id" and key != "experiment_name_hash" and key != "progressive_id" and key != 'standardized_fields':
            metabolomics_data[key] = security.decrypt_data(value)
    # rimuovi _id e experiment_name_hash
    metabolomics_data.pop("experiment_name_hash")
    return metabolomics_data, 200


# prendi tutti gli esperimenti di metabolomica di un progetto specifico
def get_metabo_experiments_by_projectId_views(project_id):
    metabolomics_data = MetabolomicsModel.find_by_project_id(project_id)

    if not metabolomics_data:
        return {"error": "Metabolomics experiments not found"}, 404
    
    metabolomics_data = list(metabolomics_data)
    skip_keys = {"project_id", "experiment_name_hash", "progressive_id", "conditions", "sample_type", "standardized_fields"}
    
    for experiment in metabolomics_data:
        experiment.pop("_id", None)
        for key, value in experiment.items():
            if key not in skip_keys and isinstance(value, (str, bytes)):
                experiment[key] = security.decrypt_data(value)
        experiment.pop("experiment_name_hash", None)
        # Ensure standardized_fields is always present
        if "standardized_fields" not in experiment:
            experiment["standardized_fields"] = {}
        
    return metabolomics_data, 200

def process_pipeline_views(username, project_id, pipeline_data):
    # Validate user and project
    response, status_code = metabolomics_helpers.validate_pipeline_data(username, project_id)
    if status_code != 200:
        return response, status_code
    
    # Parse pipeline data
    data = json.loads(pipeline_data)
    print(data)
    name = data['name']
    if 'pipeline' not in data:
        return {"error": "Invalid pipeline structure."}, 400

    pipeline_steps = data['pipeline']
    output_pipeline_data = {
        "pipeline": {
            "steps": []
        }
    }
    # This will be saved to DB, not sent to Celery
    db_pipeline_data = {
        "pipeline": {
            "steps": []
        }
    }

    for step in pipeline_steps:
        step_name = step["type"]
        parameters = step["data"]["parameters"]
        db_parameters = parameters.copy()
        if "files" in parameters:
            file_paths = []
            file_ids = []
            for file_id in parameters["files"]:
                files = MetabolomicsModel.find_by_progressive_id(file_id)
                files["metabolomics_mzML_file"] = security.decrypt_data(files["metabolomics_mzML_file"])
                file_paths.append(files["metabolomics_mzML_file"])
                file_ids.append(files["progressive_id"])
            parameters_for_celery = parameters.copy()
            parameters_for_celery["file_paths"] = file_paths
            parameters_for_celery.pop("files")
            output_pipeline_data["pipeline"]["steps"].append({
                "name": step_name,
                "parameters": parameters_for_celery
            })
            # For DB, keep both file_paths and file_ids
            db_parameters["file_paths"] = file_paths
            db_parameters["file_ids"] = file_ids
            db_parameters.pop("files")
            db_pipeline_data["pipeline"]["steps"].append({
                "name": step_name,
                "parameters": db_parameters
            })
        else:
            output_pipeline_data["pipeline"]["steps"].append({
                "name": step_name,
                "parameters": parameters
            })
            db_pipeline_data["pipeline"]["steps"].append({
                "name": step_name,
                "parameters": parameters
            })

    print(output_pipeline_data)

    # Send only output_pipeline_data to Celery
    success, message = pipeline.send_pipeline_to_processor(output_pipeline_data)
    print(success, message)
    if not success:
        return {"error": message}, 500
    else:
        # Save db_pipeline_data to the database
        pipeline_data_to_save = {
            "project_id": project_id,
            "task_id": message,
            "pipeline_data": db_pipeline_data,
            "status": "Processing",
            "name": name
        }
        result = PipelineModel.create_pipeline_data(pipeline_data_to_save)
        return {
            "message": "The pipeline is running in the background",
            "data": output_pipeline_data  # Only file_paths, no file_ids
        }, 200

    
    
def get_all_pipeline_views(username, project_id):
    # controlla che utente e progetto esistono nel database
    response, status_code = metabolomics_helpers.validate_pipeline_data(username, project_id)
    if status_code != 200:
        return response, status_code
    print("validazione del membro")
    # controlla che l'utente sia membro del progetto -> modificare username con user_id --> capire come ottenere user_id da username
    response, status_code = metabolomics_helpers.validate_user_project(username, project_id)
    if status_code != 200:
        return response, status_code
    # ritorna tutte le pipeline del progetto
    response = PipelineModel.find_by_project_id(project_id)
    response = list(response)
    # pop _id
    for pipeline in response:
        pipeline.pop("_id")
    print(response)
    return response, status_code

# views per eliminare la pipeline
def delete_pipeline_views(username, project_id, progressive_id):
    # controlla che l'utente sia registrato e PI del progetto. 
    response, status_code = metabolomics_helpers.is_user_admin(username, project_id)
    # Se l'utente è PI del progetto, può eliminare la pipeline
    if status_code != 200:
        return response, status_code
    # elimina la pipeline
    response = PipelineModel.delete_pipeline_by_id(int(progressive_id))
    if response.deleted_count > 0:
        return {"message":"The pipeline has been deleted"}, 200
    return {"error":"The pipeline does not exist"}, 404


def batch_upload_metabolomics_experiment_views(username, project_id, files, metadata_file=None):
    """
    Process multiple metabolomics files and their metadata in batch.
    
    Args:
        username: The ID of the user uploading the files
        project_id: The ID of the project
        files: List of RAW files
        metadata_file: Optional Excel/CSV file containing metadata
    
    Returns:
        tuple: (response_dict, status_code)
    """
    try:
        results = []
        duplicates = []
        
        print(username)
        
        # Process metadata file if provided
        metadata_dict = {}
        if metadata_file:
            try:
                # Read metadata file (supports both Excel and CSV)
                if metadata_file.filename.endswith('.csv'):
                    df = pd.read_csv(metadata_file)
                else:
                    df = pd.read_excel(metadata_file)
                
                # Convert DataFrame to dictionary with filename as key
                metadata_dict = df.set_index('File Name').to_dict(orient='index')
            except Exception as e:
                return {
                    "error": f"Error processing metadata file: {str(e)}"
                }, 400

        for file in files:
            try:
                # Check if file already exists for this project
                existing_experiment = MetabolomicsModel.find_by_name_and_project(
                    project_id=project_id,
                    experiment_name=file.filename
                )
                
                if existing_experiment:
                    duplicates.append(file.filename)
                    results.append({
                        "filename": file.filename,
                        "status": "Skipped - File already exists"
                    })
                    continue

                # Save the RAW file
                response, status = metabolomics_helpers.save_file(file)
                if status != 200:
                    results.append({
                        "filename": file.filename,
                        "status": f"Error saving file: {response.get('error', 'Unknown error')}"
                    })
                    continue

                # Convert RAW to mzML
                metabolomics_mzML_path = metabolomics.convert_raw_to_mzml(response)
                
                # Create experiment name hash
                experiment_name_hash = hashlib.sha256(file.filename.encode()).hexdigest()
                
                # Prepare metadata
                file_metadata = metadata_dict.get(file.filename, {}) if metadata_dict else {}
                
                # Prepare experiment data
                metabolomics_data = {
                    "project_id": project_id,
                    "metabolomics_experiment_name": file.filename,
                    "metabolomics_experiment_file": response,
                    "metabolomics_mzML_file": metabolomics_mzML_path,
                    "experiment_name_hash": experiment_name_hash,
                    "conditions": file_metadata.get('Conditions', ''),
                    "sample_type": file_metadata.get('Sample Type', '')
                }
                
                # Encrypt sensitive data
                for key, value in metabolomics_data.items():
                    if key not in ["project_id", "experiment_name_hash"] and value:
                        metabolomics_data[key] = security.encrypt_data(str(value))
                
                # Save to database
                MetabolomicsModel.create_metabolomics_data(metabolomics_data)
                
                results.append({
                    "filename": file.filename,
                    "status": "Success"
                })
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": f"Error: {str(e)}"
                })
                
        response_data = {
            "message": "Batch upload completed",
            "results": results
        }
        
        if duplicates:
            response_data["duplicates"] = duplicates
            
        return response_data, 200 if not duplicates else 409

    except Exception as e:
        return {"error": f"Error processing batch upload: {str(e)}"}, 500


# funzione per retrievare il report di una pipeline
def get_metabolomics_pipeline_result_views(username, project_id, progressive_id):
    pipeline = PipelineModel.find_by_progressive_id(int(progressive_id))
    if not pipeline:
        return {"error": "Pipeline not found"}, 404

    pipeline_data = pipeline.get("pipeline_data")
    if not pipeline_data:
        return {'error': 'There was an issue in the processing of the pipeline data'}, 500

    hmdb_search_csv = pipeline.get("hmdb_search_result", None)
    if hmdb_search_csv:
        df = pd.read_csv(hmdb_search_csv)

        # Parse and expand the hmdb_matches column
        def parse_first_compound(cell):
            try:
                compounds = ast.literal_eval(cell) if isinstance(cell, str) else []
                if isinstance(compounds, list) and len(compounds) > 0 and isinstance(compounds[0], dict):
                    first = compounds[0]
                    return pd.Series({
                        'hmdb_accession': first.get('accession', ''),
                        'hmdb_name': first.get('name', ''),
                        'hmdb_mass': first.get('mass', '')
                    })
                else:
                    return pd.Series({'hmdb_accession': '', 'hmdb_name': '', 'hmdb_mass': ''})
            except Exception:
                return pd.Series({'hmdb_accession': '', 'hmdb_name': '', 'hmdb_mass': ''})

        expanded = df['hmdb_matches'].apply(parse_first_compound)
        df = pd.concat([df, expanded], axis=1)
        print(df.head())

        # Optionally drop the original hmdb_matches column
        # df = df.drop(columns=['hmdb_matches'])

        df_json = df.to_dict(orient='records')
        return df_json, 200

    return {'message': 'The pipeline ran succesfully, but no annotation was selected as the step'}, 200
