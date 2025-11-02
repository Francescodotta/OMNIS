import os
from flask import request, jsonify, send_file
import pandas as pd
from werkzeug.utils import secure_filename
from ..models.flow_cytometry import FlowCytometryModel, ProjectModel, WorkspaceModel, FlowCytoPipelineRun, UserModel, MemberModel  # Assicurati di importare il modello corretto
from ..config import Config
from dotenv import load_dotenv
from ..helpers.flow_cytometry_helpers import encrypt_flow_cytometry_data, decrypt_flow_cytometry_data
from ..utils.security import encrypt_data
import json
from  app.utils import security, pipeline
import flowkit as fk
# import bson mongodb
from bson import ObjectId
import logging 

# Set up logging
logger = logging.getLogger("custom_info_logger")
# Carica le variabili d'ambiente dal file .env
load_dotenv()

# flow cytometry save path
FLOW_CYTOMETRY_SAVE_PATH = os.getenv('FLOW_CYTOMETRY_SAVE_PATH')

# Funzione per caricare un file di citofluorimetria
def upload_flow_cytometry_file_views(project_id, cytofluorimetry_file, description, username):
    if not cytofluorimetry_file:
        logger.error(f"No file provided by user {username}")
        return {'error': 'No file provided'}, 400

    # Verifica che il file sia valido
    if not allowed_file(cytofluorimetry_file.filename):
        logger.error(f"File type not allowed: {cytofluorimetry_file.filename}")
        return {'error': 'File type not allowed'}, 400

    # controlla che il progetto esiste
    if not ProjectModel.find_by_progressive_id(project_id):
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404
    
    # check the user
    if not UserModel.find_by_username(username):
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    user = UserModel.find_by_username(username)
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id'] ), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    
    # crea la directory per FLOW_CYTOMETRY_SAVE_PATH
    if not os.path.exists(FLOW_CYTOMETRY_SAVE_PATH):
        os.makedirs(FLOW_CYTOMETRY_SAVE_PATH)
    
    # Create project directory path
    project_directory = os.path.join(FLOW_CYTOMETRY_SAVE_PATH, f'project_{project_id}')
    
    # Create project directory if it doesn't exist
    if not os.path.exists(project_directory):
        os.makedirs(project_directory)

    # Salva il file nella directory del progetto
    filename = secure_filename(cytofluorimetry_file.filename)
    file_path = os.path.join(project_directory, filename)
    cytofluorimetry_file.save(file_path)

    # Get optional fields from request
    workspace = request.form.get('workspace', '')
    timepoint = request.form.get('timepoint', '')

    # Crea un'istanza di FlowCytometryModel con project_id
    flow_data = {
        'filename': filename,
        'user_id': user['progressive_id'],
        'project_id': project_id,
        'description': description,
        'file_path': file_path,
        'workspace': workspace,
        'timepoint': timepoint
    }

    # Encrypt the flow data before saving
    encrypted_data = encrypt_flow_cytometry_data(flow_data)
    
    # Save encrypted data to database
    flow_file = FlowCytometryModel.create_flow_cytometry_data(encrypted_data)
    # controlla che il file sia stato creato
    if not flow_file:
        logger.error(f"Failed to create file: {filename}")
        return {'error': 'File not created'}, 500

    logger.info(f"File uploaded: {filename} by user {username}")
    
    return {
        'message': 'File uploaded successfully',
        'progressive_id': str(flow_file.inserted_id),
        'file_path': file_path,
        'project_id': project_id,
        'workspace': workspace,
        'timepoint': timepoint
    }, 201

def upload_flow_cytometry_batch_files_views(project_id, cytofluorimetry_files, workspace_files, username, metadata_file=None):
    """
    Handles the batch upload of flow cytometry files and workspace files.

    Parameters:
    - project_id: ID of the project.
    - cytofluorimetry_files: List of FCS files to upload.
    - workspace_files: List of workspace files to upload.
    - username: ID of the user uploading the files.
    - metadata_file: Optional metadata file containing additional fields.

    Returns:
    - JSON response with status messages and HTTP status code.
    """
    # 1) Check that the project exists in the database
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404

    # 2) Check that the user has permissions to upload files to the project
    # check the user
    if not UserModel.find_by_username(username):
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    user = UserModel.find_by_username(username)
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403       

    # 3) Get existing filenames in the project to check for duplicates
    existing_files = FlowCytometryModel.find_by_project_id(project_id)
    existing_filenames = [decrypt_flow_cytometry_data(f)['filename'] for f in existing_files]
    
    # if there are duplicates in the uploaded files list, return an error with the file names that are duplicates
    duplicate_files = [f.filename for f in cytofluorimetry_files if f.filename in existing_filenames]
    if duplicate_files:
        logger.error(f"Duplicate files found: {duplicate_files} by user {username}")
        return {'error': 'Duplicate files found', 'duplicates': duplicate_files}, 400

    # 4) Save the files to the data storage using the flow cytometry path
    # Create project directory if it doesn't exist
    project_directory = os.path.join(FLOW_CYTOMETRY_SAVE_PATH, f'project_{project_id}')
    if not os.path.exists(project_directory):
        os.makedirs(project_directory)

    # Create workspace directory if it doesn't exist
    workspace_directory = os.path.join(FLOW_CYTOMETRY_SAVE_PATH, f'project_{project_id}', 'workspaces')
    if not os.path.exists(workspace_directory):
        os.makedirs(workspace_directory)

    # 5) If a metadata file is present, read it using pandas
    metadata_mapping = {}
    if metadata_file:
        # Determine the file extension
        metadata_filename = secure_filename(metadata_file.filename)
        ext = os.path.splitext(metadata_filename)[1].lower()
        try:
            if ext == '.csv':
                # Read CSV file
                df_metadata = pd.read_csv(metadata_file)
            elif ext in ['.xls', '.xlsx']:
                # Read Excel file
                df_metadata = pd.read_excel(metadata_file)
            else:
                logger.error(f"Unsupported metadata file format: {ext}")
                return {'error': 'Unsupported metadata file format'}, 400
        except Exception as e:
            logger.error(f"Error reading metadata file: {str(e)}")
            return {'error': f'Error reading metadata file: {str(e)}'}, 400

        # Ensure that 'Nome' column exists
        if 'nome' not in df_metadata.columns.str.lower():
            logger.error("Metadata file missing 'Nome' column")
            return {'error': 'Metadata file missing "Nome" column'}, 400

        # Build metadata mapping: filename -> metadata dict
        df_metadata.columns = df_metadata.columns.str.lower()  # Convert column names to lowercase
        df_metadata['nome'] = df_metadata['nome'].apply(secure_filename)
        
        # check that the name is equal to the name of the file
        error_files = [f.filename for f in cytofluorimetry_files if f.filename not in df_metadata['nome'].values]
        if error_files:
            # logging the files error   
            logger.error(f"Metadata file missing entries for some files: {error_files} by user {username}")
            return {'error': 'Metadata file missing entries for some files', 'files': error_files}, 400
        
        metadata_mapping = df_metadata.set_index('nome').to_dict(orient='index')

    # Initialize response list
    responses = []

    # Process each workspace file
    workspace_mapping = {}
    for workspace_file in workspace_files:
        filename = secure_filename(workspace_file.filename)

        # Save the file to the workspace directory
        file_path = os.path.join(workspace_directory, filename)
        try:
            workspace_file.save(file_path)
        except Exception as e:
            logger.error(f"Failed to save workspace file: {str(e)}")
            responses.append({'filename': filename, 'status': f'Failed to save workspace file: {str(e)}'})
            continue

        # Build workspace data dictionary
        workspace_data = {
            'filename': filename,
            'user_id': user['progressive_id'],
            'project_id': project_id,
            'file_path': file_path,
        }

        # Encrypt the workspace data before saving, excluding progressive_id and project_id
        encrypted_data = encrypt_flow_cytometry_data(workspace_data)

        # Save encrypted data to the database
        try:
            workspace_instance = WorkspaceModel.create_workspace_data(encrypted_data)
            workspace_id = workspace_instance.inserted_id
            workspace_mapping[filename] = workspace_id
            responses.append({
                'filename': filename,
                'status': 'Workspace uploaded successfully',
            })
        except Exception as e:
            logger.error(f"Failed to save workspace file data: {str(e)}")
            responses.append({'filename': filename, 'status': f'Failed to save workspace file data: {str(e)}'})

    # Process each FCS file
    for cytofluorimetry_file in cytofluorimetry_files:
        filename = secure_filename(cytofluorimetry_file.filename)

        # Check for duplicate filename
        if filename in existing_filenames:
            responses.append({'filename': filename, 'status': 'Duplicate file'})
            continue

        # Save the file to the project directory
        file_path = os.path.join(project_directory, filename)
        try:
            cytofluorimetry_file.save(file_path)
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            responses.append({'filename': filename, 'status': f'Failed to save file: {str(e)}'})
            continue

        # Get additional metadata for this file
        file_metadata = metadata_mapping.get(filename, {})

        # Associate workspace ID if available
        workspace_filename = file_metadata.get('workspace', '')
        workspace_id = workspace_mapping.get(workspace_filename, None)
        if workspace_id:
            file_metadata['workspace_id'] = workspace_id

        # Build flow data dictionary
        flow_data = {
            'filename': filename,
            'user_id': user['progressive_id'],
            'project_id': project_id,
            'file_path': file_path,
            # Add any additional fields from metadata
            **file_metadata
        }

        # Encrypt the flow data before saving, excluding progressive_id and project_id
        encrypted_data = encrypt_flow_cytometry_data(flow_data)

        # Save encrypted data to the database
        try:
            flow_file = FlowCytometryModel.create_flow_cytometry_data(encrypted_data)
            responses.append({
                'filename': filename,
                'status': 'Uploaded successfully',
            })
        except Exception as e:
            logger.error(f"Failed to save file data: {str(e)}")
            responses.append({'filename': filename, 'status': f'Failed to save file data: {str(e)}'})

    logger.info(f"Batch upload completed by user {username} with the following list of responses: {responses}")
    
    return {
        'message': 'Batch upload completed',
        'results': responses
    }, 200

# Funzione per ottenere un file di citofluorimetria tramite ID --> aggiungere il project_id
def get_flow_cytometry_file_views(progressive_id, username):
    
    # check the project
    flow_cytometry_file = FlowCytometryModel.find_by_progressive_id(progressive_id)
    if not flow_cytometry_file:
        logger.error(f"File not found: {progressive_id}")
        return {'error': 'File not found'}, 404

    if flow_cytometry_file['user_id'] != username:
        logger.error(f"Unauthorized access to file: {progressive_id}")
        return {'error': 'Unauthorized'}, 403

    # Decrypt the data before sending to frontend
    decrypted_data = decrypt_flow_cytometry_data(flow_cytometry_file)
    # pop the _id and workspace_id if present
    decrypted_data.pop("_id")
    if "workspace_id" in decrypted_data:
        decrypted_data.pop("workspace_id")
    print(decrypted_data)   
    logger.info(f"File retrieved: {decrypted_data['filename']} by user {username}")
    return jsonify({
        "message": "File retrieved successfully",
        "data": decrypted_data
    }), 200

# Funzione per ottenere tutti i file di citofluorimetria di un progetto specifico
def get_flow_cytometry_files_views(project_id, username):
    
    # check the project
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404
    
    # check the user
    if not UserModel.find_by_username(username):
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    user = UserModel.find_by_username(username)
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    
    files = list(FlowCytometryModel.find_by_project_id(project_id))
    if len(files) == 0:
        logger.info(f"No files found for project {project_id} by user {username}")
        return {
            'message': 'No files found',
            'data': [],
            'isEmpty': True
        }, 200
    
    # Decrypt each file's data before sending to frontend
    decrypted_files = []
    for file in files:
        try:
            decrypted_data = decrypt_flow_cytometry_data(file)
            decrypted_files.append({
                'progressive_id': str(decrypted_data['progressive_id']),
                'filename': decrypted_data['filename'],
                'file_path': decrypted_data['file_path'],
                'project_id': str(decrypted_data['project_id']),
                'workspace': decrypted_data.get('workspace', ''),
                'timepoint': decrypted_data.get('timepoint', '')
            })
        except Exception as e:
            logger.error(f"Error decrypting file data: {str(e)}")
            print(f"Error decrypting file data: {str(e)}")
            continue
    
    logger.info(f"Files retrieved for project {project_id} by user {username}")
    
    return {
        'message': 'Files retrieved successfully',
        'data': decrypted_files,
        'isEmpty': False
    }, 200

# Funzione per aggiornare i metadati di un file di citofluorimetria --> manca il project id
def update_flow_cytometry_file_views(progressive_id, data, username):
    file = FlowCytometryModel.find_by_object_id(progressive_id)
    if not file:
        logger.error(f"File not found: {progressive_id} by user {username}")
        return {'error': 'File not found'}, 404

    if file['user_id'] != username:
        logger.error(f"Unauthorized access to file: {progressive_id} by user {username}")
        return {'error': 'Unauthorized'}, 403

    # Encrypt the update data before saving
    update_data = {}
    if 'description' in data:
        encrypted_description = encrypt_data(data['description']).decode()
        update_data['description'] = encrypted_description
    
    FlowCytometryModel.update(progressive_id, update_data)
    
    logger.info(f"File updated: {progressive_id} by user {username}")
    
    return {'message': 'File updated successfully'}, 200

# Funzione per eliminare un file di citofluorimetria--> manca il project id
def delete_flow_cytometry_file_views(progressive_id, username):
    flow_cytometry_file = FlowCytometryModel.find_by_progressive_id(progressive_id)
    print(flow_cytometry_file)
    
    if not flow_cytometry_file:
        logger.error(f"File not found: {progressive_id} by user {username}")
        return {'error': 'File not found'}, 404

    if flow_cytometry_file['user_id'] != username:
        logger.error(f"Unauthorized access to file: {progressive_id} by user {username}")
        return {'error': 'Unauthorized'}, 403

    try:
        # Elimina il file dal filesystem
        if os.path.exists(flow_cytometry_file['file_path']):
            os.remove(flow_cytometry_file['file_path'])
            
            # Get the project directory path
            project_directory = os.path.dirname(flow_cytometry_file['file_path'])
            
            # If the project directory is empty after file deletion, optionally remove it
            if os.path.exists(project_directory) and not os.listdir(project_directory):
                os.rmdir(project_directory)

        # Elimina i metadati dal database
        FlowCytometryModel.delete_by_progressive_id(progressive_id)
        
        logger.info(f"File deleted: {flow_cytometry_file['filename']} by user {username}")
        
        return {
            'message': 'File deleted successfully',
            'deleted_file': flow_cytometry_file['filename'],
            'project_id': str(flow_cytometry_file['project_id'])
        }, 200
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return {
            'error': f'Error deleting file: {str(e)}'
        }, 500

# Funzione per verificare se il file è consentito
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS 
           
# funzione per processare il file di citofluorimetria
def process_flow_cytometry_file_views(username, project_id, progressive_id):
    
    # controlla che il progetto esista
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return {"error": "Project not found"}, 404
    
    user = UserModel.find_by_username(username)
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    

    # controlla che il file esista
    file = FlowCytometryModel.find_by_progressive_id(progressive_id)
    if not file:
        logger.error(f"File not found: {progressive_id} by user {username}")
        return {"error": "File not found"}, 404

    # controlla che il file appartenga al progetto
    if file["project_id"] != project_id:
        logger.error(f"File does not belong to project: {progressive_id} by user {username}")
        return {"error": "File not found in project"}, 404
    
    # prendi il file utilizzando flowkit con il flow cytometry path
    file_path = security.decrypt_data(file["file_path"])
    sample = fk.Sample(file_path)
    data = sample.as_dataframe(source = "raw", subsample = 100)
    dataset = {
        "parameters":  data.columns.tolist(),
        "data": data.to_dict(orient="records")
    }
    
    logger.info(f"File processed: {file['filename']} by user {username}")
    
    return jsonify(dataset), 200

# save pipeline in the database 
def save_flow_cytometry_pipeline_views(username, project_id, pipeline_data):
    # check the project
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404
    
    # check that the user exists
    if not UserModel.find_by_username(username):
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    user = UserModel.find_by_username(username)
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    
    # check if the project exists
    message, status_code = pipeline.save_flow_cytometry_pipeline_views(username, project_id, pipeline_data)
    return message, status_code

# crea una funzione per processare la pipeline passata dal frontend
def process_pipeline_flowCytometry_views(username, project_id, pipeline_data):
    
    # controlla che il progetto sia esistente
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {"error": "Project not found"}, 404
    
    # check the user
    if not UserModel.find_by_username(username):
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    user = UserModel.find_by_username(username)
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    
    # load dei dati della pipeline
    data = json.loads(pipeline_data)
    
    # Assicurati che la struttura contenga 'pipeline'
    if 'pipeline' not in data:
        return {"error": "Invalid pipeline structure."}, 400
    
    # estrai gli step della pipeline
    pipeline_name = data['name']
    pipeline_steps = data['pipeline']

    # costruisci l'output della pipeline
    output_pipeline_data = {
        "name": pipeline_name,
        "pipeline": {
            "steps": []  # Initialize the steps list
        }    
    }
    
    for step in pipeline_steps:
        step_name = step["type"]  # Use the 'type' as the step name
        parameters = step["data"]["parameters"]  # Extract parameters from the 'data' field
        if "select_fcs_files" in step_name:
            # se la lista dei file è vuota ritorna un errore
            if parameters is None: 
                return {"error": "No files selected"}, 400
            file_paths = []
            for file_id in parameters["files"]:
                # prendi i file dall'id
                files = FlowCytometryModel.find_by_progressive_id(int(file_id))
                # decripta il file
                files["file_path"] = security.decrypt_data(files["file_path"])
                file_paths.append(files["file_path"])
            parameters["file_paths"] = file_paths
            parameters.pop("files")
        # Aggiungi il passo alla lista
        output_pipeline_data["pipeline"]["steps"].append({
            "name": step_name,
            "parameters": parameters
        })
        
        
    # debugging
    print(output_pipeline_data)
    # Send the pipeline to the processor service
    response, message = pipeline.send_pipeline_to_processor(output_pipeline_data)
    

    print(f"Response from processor: {response}, Message: {message}")
    
    if not response:
        return {"error": message}, 500
    
    
    # add the chain ID into the output pipeline data
    output_pipeline_data["chain_id"] = response["chain_id"]

    # add the project id
    output_pipeline_data["project_id"] = project_id
    
    # save the pipeline run in the database 
    message, status_code = pipeline.save_flow_cytometry_pipeline_run_views(username, project_id, output_pipeline_data, 'processing')
    
    # drop the object id from the output pipeline data
    output_pipeline_data.pop("_id")
    
    return {"message": "The pipeline is running in the background", "data": output_pipeline_data}, 200
    
    # la pipeline è un JSON con i seguenti campi:            
                    
# function to get the details of the all the pipeline runs for a specific project id
def get_fc_pipeline_run_by_project_id_views(project_id, username):
    # check the project
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404
    
    # check the user
    if not UserModel.find_by_username(username):
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    user = UserModel.find_by_username(username)
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    # get all the pipeline runs for the project
    pipeline_runs = FlowCytoPipelineRun.find_by_project_id(project_id)
    
    # handle the cursor object
    pipeline_runs = list(pipeline_runs)
    
    # if there are no pipeline runs found
    if len(pipeline_runs) == 0:
        logger.info(f"No pipeline runs found for project {project_id} by user {username}")
        return jsonify({"message": "No pipeline runs found"}), 200
    
    # pop the _id of the pipeline runs
    for pipeline_run in pipeline_runs:
        if '_id' in pipeline_run:
            pipeline_run.pop('_id')
        for key, value in pipeline_run.items():
            if isinstance(value, ObjectId):
                pipeline_run[key] = str(value)
    
    logger.info (f"Pipeline runs retrieved for project {project_id} by user {username}")
    
    # return the pipeline runs
    return jsonify({"data":pipeline_runs}), 200

# function to get the results of the pipeline run
def get_fc_pipeline_run_results(project_id, progressive_id, username):
    # check the project id exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404
    
    # check the user
    if not UserModel.find_by_username(username):
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    user = UserModel.find_by_username(username)
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    
    # get the pipeline run by the progressive id
    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    
    # check if the pipeline run exists
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404
    
    # get all the fields that have "path" in the name
    paths = {key: pipeline_run[key] for key in pipeline_run if "path" in key}
    
    # read all the csv files and return the data
    data = {}
    for key, value in paths.items():
        try:
            df = pd.read_csv(value)
            # get maximum number of rows to 30000
            df = df.sample(n=10000, random_state=4242) if len(df) > 10000 else df
            # Convert DataFrame to dictionary while preserving all columns
            data[key] = df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error processing file {key}: {str(e)}")
            data[key] = str(e)

    # take only the clustering_result_path from the key
    clustering_result_data = {}
    for key, value in data.items():
        if "clustering_result_path" in key:
            clustering_result_data[key] = value
    
    logger.info(f"Pipeline run results retrieved for project {project_id} by user {username}")    
    
    return jsonify({"data": clustering_result_data}), 200

# views to get the fcs heatmap data
def get_fc_pipeline_run_heatmap_results_views(project_id, progressive_id, username):
    # check the project id exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404
    
    # check the user
    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return jsonify({"error": "User does not have permissions for project"}), 403
    
    # get the pipeline run by the progressive id
    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    
    # check if the pipeline run exists
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404
    
    # get the heatmap csv file
    df = pd.read_csv(pipeline_run["heatmap_data_path"])
        
    # transform data into a dictionary
    heatmap_data = df.to_dict(orient="records")
    
    logger.info(f"Heatmap data retrieved for project {project_id} by user {username}")
    
    return jsonify({"data": heatmap_data}), 200

# get all the information about a specific flow cytometry object
def get_fcs_object_views(progressive_id, project_id, username):
    # check that the project id exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404
    
    # check the user
    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return jsonify({"error": "User does not have permissions for project"}), 403
    
    # get the flow cytometry object by the progressive id
    fcs_object = FlowCytometryModel.find_by_progressive_id(progressive_id)
    
    # check if the flow cytometry object exists
    if not fcs_object:
        logger.error(f"Flow cytometry object not found: {progressive_id} by user {username}")
        return jsonify({"error": "Flow cytometry object not found"}), 404
    
    # decrypt all the fields and remove the _id and workspace_id if present
    for key, value in fcs_object.items():
        if key != "_id" and key != "workspace_id":
            fcs_object[key] = security.decrypt_data(value)
    
    # remove the _id and workspace_id from the flow cytometry object
    fcs_object.pop("_id")
    fcs_object.pop("workspace_id")
    
    # return the flow cytometry object
    return jsonify({"data": fcs_object}), 200

