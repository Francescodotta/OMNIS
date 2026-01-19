import os
from flask import request, jsonify, send_file
import pandas as pd
from werkzeug.utils import secure_filename
from ..models.flow_cytometry import FlowCytometryModel, ProjectModel, WorkspaceModel, FlowCytoPipelineRun, UserModel, MemberModel  # Assicurati di importare il modello corretto
from ..config import Config
from dotenv import load_dotenv
from ..helpers.flow_cytometry_helpers import encrypt_flow_cytometry_data, decrypt_flow_cytometry_data, safe_decrypt
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
def upload_flow_cytometry_file_views(project_id, cytofluorimetria_file, description, username):
    if not cytofluorimetria_file:
        logger.error(f"No file provided by user {username}")
        return {'error': 'No file provided'}, 400

    # Verifica che il file sia valido
    if not allowed_file(cytofluorimetria_file.filename):
        logger.error(f"File type not allowed: {cytofluorimetria_file.filename}")
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
    filename = secure_filename(cytofluorimetria_file.filename)
    file_path = os.path.join(project_directory, filename)
    cytofluorimetria_file.save(file_path)

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

def upload_flow_cytometry_batch_files_views(project_id, cytofluorimetria_files, workspace_files, username, metadata_file=None):
    """
    Handles the batch upload of flow cytometry files and workspace files.

    Parameters:
    - project_id: ID of the project.
    - cytofluorimetria_files: List of FCS files to upload.
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
    existing_filenames = []
    for f in existing_files:
        try:
            dec = decrypt_flow_cytometry_data(f)
            fname = dec.get('filename')
            if fname:
                existing_filenames.append(fname)
        except Exception as e:
            logger.debug("Skipping file during duplicate check, decryption failed: %s", str(e))

    # if there are duplicates in the uploaded files list, return an error with the file names that are duplicates
    duplicate_files = [f.filename for f in cytofluorimetria_files if f.filename in existing_filenames]
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
        
        # Normalize filenames in the metadata file
        df_metadata['nome'] = df_metadata['nome'].apply(lambda x: secure_filename(x).replace(" ", "_").lower())

        # Normalize filenames in the uploaded files
        uploaded_filenames = [secure_filename(f.filename).replace(" ", "_").lower() for f in cytofluorimetria_files]

        # Check for missing files
        error_files = [f for f in uploaded_filenames if f not in df_metadata['nome'].values]
        if error_files:
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
    for cytofluorimetria_file in cytofluorimetria_files:
        filename = secure_filename(cytofluorimetria_file.filename)
        
        # Normalize filename for metadata lookup (same normalization as metadata file)
        normalized_filename = filename.replace(" ", "_").lower()

        # Check for duplicate filename
        if filename in existing_filenames:
            responses.append({'filename': filename, 'status': 'Duplicate file'})
            continue

        # Save the file to the project directory
        file_path = os.path.join(project_directory, filename)
        try:
            cytofluorimetria_file.save(file_path)
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            responses.append({'filename': filename, 'status': f'Failed to save file: {str(e)}'})
            continue

        # Get additional metadata for this file using normalized filename
        file_metadata = metadata_mapping.get(normalized_filename, {})

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
            # remove _id
            decrypted_data.pop("_id")
            decrypted_data.pop("workspace_id", None)
            decrypted_files.append(decrypted_data)
            # add unpacked other metadata within the forms
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
    
    if not flow_cytometry_file:
        logger.error(f"File not found: {progressive_id} by user {username}")
        return {'error': 'File not found'}, 404

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
        

def delete_batch_flow_cytometry_files_views(project_id, file_ids, username):    
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
    
    deleted_files = []
    errors = []
    
    for file_id in file_ids:
        flow_cytometry_file = FlowCytometryModel.find_by_progressive_id(file_id)
        
        # decrypt data
        flow_cytometry_file = decrypt_flow_cytometry_data(flow_cytometry_file)
        
        if not flow_cytometry_file:
            errors.append({'file_id': file_id, 'error': 'File not found'})
            continue

        try:
            # Elimina il file dal filesystem
            if os.path.exists(flow_cytometry_file['file_path']):
                # decrypt the file path
                
                os.remove(flow_cytometry_file['file_path'])
                
                # Get the project directory path
                project_directory = os.path.dirname(flow_cytometry_file['file_path'])
                
                # If the project directory is empty after file deletion, optionally remove it
                if os.path.exists(project_directory) and not os.listdir(project_directory):
                    os.rmdir(project_directory)

            # Elimina i metadati dal database
            FlowCytometryModel.delete_by_progressive_id(file_id)
            deleted_files.append(flow_cytometry_file['filename'])
        except Exception as e:
            errors.append({'file_id': file_id, 'error': str(e)})
    
    logger.info(f"Batch file deletion completed by user {username}. Deleted files: {deleted_files}, Errors: {errors}")
    
    return {
        'message': 'Batch file deletion completed',
        'deleted_files': deleted_files,
        'errors': errors
    }, 200
        
        
        

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
    print(data)
    
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
    
    STANDARD_FIELDS = ["file_id", "file_path", "filename"]

    for step in pipeline_steps:
        step_name = step["type"]
        parameters = step["data"]["parameters"]
        if "select_fcs_files" in step_name:
            if parameters is None:
                return {"error": "No files selected"}, 400
            files_info = []
            for file_id in parameters["files"]:
                file_obj = FlowCytometryModel.find_by_progressive_id(int(file_id))
                # drop the _id and workspace_id
                file_obj.pop("_id", None)
                file_obj.pop("workspace_id", None)
                # Decrypt all fields
                decrypted = {k: safe_decrypt(v) if isinstance(v, str) else v for k, v in file_obj.items()}
                # Standard fields
                file_info = {
                    "file_id": file_id,
                    "file_path": decrypted.get("file_path"),
                    "filename": decrypted.get("filename"),
                }
                # Dynamic metadata: everything else
                file_info["metadata"] = {k: v for k, v in decrypted.items() if k not in ["_id", "file_path", "filename", "progressive_id"]}
                files_info.append(file_info)
            parameters["files_info"] = files_info
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
    print("Saving pipeline run in the database...\n\n")
    print(output_pipeline_data) 
    message, status_code = pipeline.save_flow_cytometry_pipeline_run_views(username, project_id, output_pipeline_data)
    
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

def get_fc_pipeline_umap_results(project_id, progressive_umap_id, username):
    print(project_id, progressive_umap_id)
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404
    # check the user
    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404
    # get the Pipeline from FlowCytoPipelineRun by the progressive_umap_id
    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(int(progressive_umap_id))
    # check if the pipeline run exists
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_umap_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404
    
    # if umap_results_path is not present in the pipeline run
    if "umap_results_path" not in pipeline_run:
        # return a None to the frontend to let the user know that there are no umap results
        logger.info(f"No UMAP results found for pipeline run: {progressive_umap_id} by user {username}")
        return jsonify({"data": None}), 200
    # get the umap csv file
    df = pd.read_csv(pipeline_run["umap_results_path"], sep="\t")
    # drop project_id and sample_id from columns
    df = df.drop(columns=["project_id", "sample_id"], errors='ignore')
    # if dataset is too large (> 100000 rows), try to sample it maintaining the distribution
    # print len of the df
    print(len(df))
    if len(df) > 8000:
        df = df.sample(n=8000, random_state=4242)
    # transform data into a dictionary
    umap_data = df.to_dict(orient="records")
    logger.info(f"UMAP data retrieved for project {project_id} by user {username}")
    return jsonify({"data": umap_data}), 200


def get_fc_pipeline_cohen(project_id, progressive_id, username):
    # permission checks
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404

    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404

    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return jsonify({"error": "User does not have permissions for project"}), 403

    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404

    # prefer the pairwise metrics CSV produced by pairwise analysis
    cohen_path = pipeline_run.get("pairwise_metrics_path_csv") or pipeline_run.get("cohen_data_path") or pipeline_run.get("cohen_path")
    if not cohen_path or not os.path.exists(cohen_path):
        logger.info(f"Cohen metrics file not available for pipeline {progressive_id}")
        return jsonify({"data": None}), 200

    try:
        sep = '\t' if cohen_path.lower().endswith(('.tsv', '.txt')) else ','
        df = pd.read_csv(cohen_path, sep=sep)
        # sample if too large
        if len(df) > 20000:
            df = df.sample(n=20000, random_state=4242)
        cohen_data = df.to_dict(orient="records")
        logger.info(f"Cohen data retrieved for project {project_id} by user {username}")
        return jsonify({"data": cohen_data}), 200
    except Exception as e:
        logger.error(f"Error reading Cohen data {cohen_path}: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_fc_pipeline_volcano(project_id, progressive_id, username):
    # permission checks
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404

    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404

    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return jsonify({"error": "User does not have permissions for project"}), 403

    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404

    # Check for CSV data first, then for an image/plot path
    csv_path = pipeline_run.get("volcano_data_path") or pipeline_run.get("csv_volcano_data")
    plot_path = pipeline_run.get("volcano_plot_path") or pipeline_run.get("volcano_path")

    if csv_path and os.path.exists(csv_path):
        try:
            sep = '\t' if csv_path.lower().endswith(('.tsv', '.txt')) else ','
            df = pd.read_csv(csv_path, sep=sep)
            if len(df) > 20000:
                df = df.sample(n=20000, random_state=4242)
            volcano_data = df.to_dict(orient="records")
            logger.info(f"Volcano CSV data retrieved for project {project_id} by user {username}")
            return jsonify({"data": volcano_data}), 200
        except Exception as e:
            logger.error(f"Error reading volcano CSV {csv_path}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    if plot_path and os.path.exists(plot_path):
        # return info about the image (frontend can request the file endpoint or use a dedicated route)
        logger.info(f"Volcano plot available for pipeline {progressive_id}")
        return jsonify({"data": {"image": os.path.basename(plot_path), "path": plot_path}}), 200

    logger.info(f"No volcano results available for pipeline {progressive_id}")
    return jsonify({"data": None}), 200

def get_fc_pipeline_heatmap_differences(project_id, progressive_id, username):
    # permission checks
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404

    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404

    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return jsonify({"error": "User does not have permissions for project"}), 403

    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404

    # prefer the CSV differences path generated in pairwise analysis
    heatmap_csv = pipeline_run.get("heatmap_difference_path_csv") or pipeline_run.get("heatmap_differences") or pipeline_run.get("heatmap_data_path")
    print(heatmap_csv)
    # also support image path(s)
    heatmap_image = pipeline_run.get("heatmap_difference_path") or pipeline_run.get("stat_heatmap_path")

    if heatmap_csv and os.path.exists(heatmap_csv):
        try:
            sep = '\t' if heatmap_csv.lower().endswith(('.tsv', '.txt')) else ','
            df = pd.read_csv(heatmap_csv, sep=sep)
            if len(df) > 20000:
                df = df.sample(n=20000, random_state=4242)
            heatmap_diff_data = df.to_dict(orient="records")
            logger.info(f"Heatmap difference CSV retrieved for project {project_id} by user {username}")
            return jsonify({"data": heatmap_diff_data}), 200
        except Exception as e:
            logger.error(f"Error reading heatmap CSV {heatmap_csv}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    if heatmap_image:
        # if image exists, return its filename/path for frontend to request via file endpoint
        logger.info(f"Heatmap image available for pipeline {progressive_id}")
        return jsonify({"data": {"image": os.path.basename(heatmap_image), "path": heatmap_image}}), 200

    logger.info(f"No heatmap differences available for pipeline {progressive_id}")
    return jsonify({"data": None}), 200

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

def set_control_id_view(project_id, sample_id, control_id):
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404
    
    # check that the sample exists
    sample = FlowCytometryModel.find_by_progressive_id(sample_id)
    if not sample:
        logger.error(f"Sample not found: {sample_id}")
        return {'error': 'Sample not found'}, 404
    
    # check that the control sample exists
    control_sample = FlowCytometryModel.find_by_progressive_id(control_id)
    if not control_sample:
        logger.error(f"Control sample not found: {control_id}")
        return {'error': 'Control sample not found'}, 404
    
    # update the sample with the control id
    FlowCytometryModel.set_control_id(sample_id, control_id)
    logger.info(f"Control ID {control_id} set for sample {sample_id} in project {project_id}")
    print(f"Control ID {control_id} set for sample {sample_id} in project {project_id}")
    return {'message': 'Control ID set successfully'}, 200



def assign_standardized_fields_view(project_id, experiment_id, fields, username):
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404
    
    # check that the experiment exists
    experiment = FlowCytometryModel.find_by_progressive_id(experiment_id)
    if not experiment:
        logger.error(f"Experiment not found: {experiment_id}")
        return {'error': 'Experiment not found'}, 404
    
    # check that the user exists
    user = UserModel.find_by_username(username)
    if not user:
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    
    # assign standardized fields to the experiment
    update_fields = experiment.get('standardized_fields', {})
    update_fields.update(fields)
    message = FlowCytometryModel.update(experiment_id, {'standardized_fields': update_fields})
    if message:
        logger.info(f"Standardized fields assigned to experiment {experiment_id} in project {project_id} by user {username}")
        print(f"Standardized fields assigned to experiment {experiment_id} in project {project_id} by user {username}")
        status_code = 200
    else:
        logger.error(f"Failed to assign standardized fields to experiment {experiment_id} in project {project_id} by user {username}")
        print(f"Failed to assign standardized fields to experiment {experiment_id} in project {project_id} by user {username}")
        status_code = 500
    return message, status_code


def bulk_assign_standardized_fields_view(project_id, assignments, username):
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404
    
    # check that the user exists
    user = UserModel.find_by_username(username)
    if not user:
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    
    # iterate over the assignments and assign standardized fields
    for assignment in assignments:
        experiment_id = assignment.get('experiment_id')
        fields = assignment.get('fields', {})
        
        # check that the experiment exists
        experiment = FlowCytometryModel.find_by_progressive_id(experiment_id)
        if not experiment:
            logger.error(f"Experiment not found: {experiment_id}")
            continue
        
        # assign standardized fields to the experiment
        update_fields = experiment.get('standardized_fields', {})
        update_fields.update(fields)
        FlowCytometryModel.update(experiment_id, {'standardized_fields': update_fields})
        logger.info(f"Standardized fields assigned to experiment {experiment_id} in project {project_id} by user {username}")
    
    return {'message': 'Bulk standardized fields assignment completed'}, 200


def delete_pipelinerun_by_progressive_id(project_id, progressive_id, username):
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        return {'error': 'Project not found'}, 404
    
    # check that the user exists
    user = UserModel.find_by_username(username)
    if not user:
        logger.error(f"User not found: {username}")
        return {'error': 'User not found'}, 404
    
    # check the membership of the user
    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return {'error': 'User does not have permissions for project'}, 403
    
    # 🦍 FIX: Verifica che la pipeline run esista prima di eliminarla
    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id}")
        return {'error': 'Pipeline run not found'}, 404
    
    # 🦍 FIX: Elimina i file dei risultati se esistono
    paths_to_delete = [
        pipeline_run.get('umap_results_path'),
        pipeline_run.get('clustering_result_path'),
        pipeline_run.get('heatmap_data_path')
    ]
    
    for file_path in paths_to_delete:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted result file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {str(e)}")
    
    # 🦍 FIX: Elimina la pipeline run dal database
    try:
        result = FlowCytoPipelineRun.delete_by_progressive_id(progressive_id)
        if result:
            logger.info(f"Pipeline run {progressive_id} deleted successfully by user {username}")
            return {'message': 'Pipeline run deleted successfully'}, 200
        else:
            logger.error(f"Failed to delete pipeline run {progressive_id}")
            return {'error': 'Failed to delete pipeline run'}, 500
    except Exception as e:
        logger.error(f"Error deleting pipeline run {progressive_id}: {str(e)}")
        return {'error': f'Error deleting pipeline run: {str(e)}'}, 500



def get_fc_pipeline_cohen(project_id, progressive_id, username):
    # permission checks
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404

    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404

    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return jsonify({"error": "User does not have permissions for project"}), 403

    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404

    # prefer the pairwise metrics CSV produced by pairwise analysis
    cohen_path = pipeline_run.get("pairwise_metrics_path_csv") or pipeline_run.get("cohen_data_path") or pipeline_run.get("cohen_path")
    if not cohen_path or not os.path.exists(cohen_path):
        logger.info(f"Cohen metrics file not available for pipeline {progressive_id}")
        return jsonify({"data": None}), 200

    try:
        sep = '\t' if cohen_path.lower().endswith(('.tsv', '.txt')) else ','
        df = pd.read_csv(cohen_path, sep=sep)
        # sample if too large
        if len(df) > 20000:
            df = df.sample(n=20000, random_state=4242)
        cohen_data = df.to_dict(orient="records")
        logger.info(f"Cohen data retrieved for project {project_id} by user {username}")
        return jsonify({"data": cohen_data}), 200
    except Exception as e:
        logger.error(f"Error reading Cohen data {cohen_path}: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_fc_pipeline_volcano(project_id, progressive_id, username):
    # permission checks
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404

    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404

    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return jsonify({"error": "User does not have permissions for project"}), 403

    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404

    # Check for CSV data first, then for an image/plot path
    csv_path = pipeline_run.get("volcano_data_path") or pipeline_run.get("csv_volcano_data")
    plot_path = pipeline_run.get("volcano_plot_path") or pipeline_run.get("volcano_path")

    if csv_path and os.path.exists(csv_path):
        try:
            sep = '\t' if csv_path.lower().endswith(('.tsv', '.txt')) else ','
            df = pd.read_csv(csv_path, sep=sep)
            if len(df) > 20000:
                df = df.sample(n=20000, random_state=4242)
            volcano_data = df.to_dict(orient="records")
            logger.info(f"Volcano CSV data retrieved for project {project_id} by user {username}")
            return jsonify({"data": volcano_data}), 200
        except Exception as e:
            logger.error(f"Error reading volcano CSV {csv_path}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    if plot_path and os.path.exists(plot_path):
        # return info about the image (frontend can request the file endpoint or use a dedicated route)
        logger.info(f"Volcano plot available for pipeline {progressive_id}")
        return jsonify({"data": {"image": os.path.basename(plot_path), "path": plot_path}}), 200

    logger.info(f"No volcano results available for pipeline {progressive_id}")
    return jsonify({"data": None}), 200

def get_fc_pipeline_heatmap_differences(project_id, progressive_id, username):
    # permission checks
    project = ProjectModel.find_by_progressive_id(project_id)
    if not project:
        logger.error(f"Project not found: {project_id} by user {username}")
        return jsonify({"error": "Project not found"}), 404

    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User not found: {username}")
        return jsonify({"error": "User not found"}), 404

    membership = MemberModel.find_by_user_id_project_id(int(user['progressive_id']), int(project_id))
    if membership is None:
        logger.error(f"User does not have permissions for project: {project_id}")
        return jsonify({"error": "User does not have permissions for project"}), 403

    pipeline_run = FlowCytoPipelineRun.find_by_progressive_id(progressive_id)
    if not pipeline_run:
        logger.error(f"Pipeline run not found: {progressive_id} by user {username}")
        return jsonify({"error": "Pipeline run not found"}), 404

    # prefer the CSV differences path generated in pairwise analysis
    heatmap_csv = pipeline_run.get("heatmap_difference_path_csv") or pipeline_run.get("heatmap_differences") or pipeline_run.get("heatmap_data_path")
    print(heatmap_csv)
    # also support image path(s)
    heatmap_image = pipeline_run.get("heatmap_difference_path") or pipeline_run.get("stat_heatmap_path")

    if heatmap_csv and os.path.exists(heatmap_csv):
        try:
            sep = '\t' if heatmap_csv.lower().endswith(('.tsv', '.txt')) else ','
            df = pd.read_csv(heatmap_csv, sep=sep)
            if len(df) > 20000:
                df = df.sample(n=20000, random_state=4242)
            heatmap_diff_data = df.to_dict(orient="records")
            logger.info(f"Heatmap difference CSV retrieved for project {project_id} by user {username}")
            return jsonify({"data": heatmap_diff_data}), 200
        except Exception as e:
            logger.error(f"Error reading heatmap CSV {heatmap_csv}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    if heatmap_image:
        # if image exists, return its filename/path for frontend to request via file endpoint
        logger.info(f"Heatmap image available for pipeline {progressive_id}")
        return jsonify({"data": {"image": os.path.basename(heatmap_image), "path": heatmap_image}}), 200

    logger.info(f"No heatmap differences available for pipeline {progressive_id}")
    return jsonify({"data": None}), 200

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