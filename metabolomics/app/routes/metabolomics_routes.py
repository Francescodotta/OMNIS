import app.views.metabo_experiment_views as metabolomics_views
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity, create_access_token
import json

bp = Blueprint('metabolomics', __name__)
# logger = logging.getLogger("custom_info_logger")
# bisogna fare il setup del logger anche per questo microservizio



# route per fare l'upload di esperimenti di metabolomica
@bp.route('/api/project/<project_id>/metabolomics', methods=['POST'])
@jwt_required()
def upload_metabolomics_experiment(project_id):
    # prendi i dati dall'utente
    user_id = get_jwt_identity()
    experimentName = request.form.get("experimentName")
    # prendi il file
    metabolomics_file = request.files["file"]
    # fai il view
    result, status_code = metabolomics_views.upload_metabolomics_experiment_views(user_id, project_id, experimentName, metabolomics_file)
    return jsonify(result), status_code


# route to upload multiple metabolomics experiments
@bp.route('/api/v1/project/<project_id>/metabolomics_experiments', methods=['POST'])
@jwt_required()
def batch_upload_metabolomics_experiments(project_id):
    print(project_id)
    # Get user ID from JWT token
    user_id = get_jwt_identity()
    
    # Check if files were provided
    if 'metabolomics_files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
        
    # Get list of files and metadata file
    files = request.files.getlist('metabolomics_files')
    metadata_file = request.files.get('metadata_file')
    
    # Validate file types
    for file in files:
        if not file.filename.lower().endswith('.raw'):
            return jsonify({
                "error": f"Invalid file type for {file.filename}. Only .raw files are accepted."
            }), 400
    
    # If metadata file is provided, validate its type
    if metadata_file and not metadata_file.filename.lower().endswith(('.csv', '.xls', '.xlsx')):
        return jsonify({
            "error": "Invalid metadata file type. Only .csv, .xls, or .xlsx files are accepted."
        }), 400
    
    # Process the batch upload
    result, status_code = metabolomics_views.batch_upload_metabolomics_experiment_views(
        username=user_id,
        project_id=project_id,
        files=files,
        metadata_file=metadata_file
    )
    
    return jsonify(result), status_code

# route per leggere un esperimento di metabolomica
@bp.route('/api/metabolomics/<metabolomics_id>', methods=['GET'])
def read_metabolomics_experiment(metabolomics_id):
    result, status_code = metabolomics_views.get_metabolomics_experiment_views(int(metabolomics_id))
    return jsonify(result), status_code 

# route per leggere tutti gli esperimenti di metabolomica di un progetto
@bp.route('/api/project/<project_id>/metabolomics', methods=['GET'])
def read_metabo_experiments_by_projectId(project_id):
    result, status_code = metabolomics_views.get_metabo_experiments_by_projectId_views(project_id)
    return jsonify(result), status_code


# route per la gestione di pipeline di metabolomica
@bp.route('/api/project/<project_id>/process_pipeline', methods=['POST'])
@jwt_required()
def process_pipeline_metabolomics(project_id):
    # prendi i dati dall'utente
    user_id = get_jwt_identity()
    data = request.get_json()
    print('request received')
    pipe_data = data.get("body")
    result, status_code = metabolomics_views.process_pipeline_views(user_id, project_id, pipe_data)
    return jsonify(result), status_code

# route per salvare la pipeline
@bp.route('/api/project/<project_id>/pipeline', methods=['POST'])
@jwt_required()
def save_pipeline_metabolomics(project_id):
    # prendi i dati dall'utente
    user_id = get_jwt_identity()
    data = request.get_json()
    pipe_data = data.get("body")
    result, status_code = metabolomics_views.save_pipeline_views(user_id, project_id, pipe_data)
    return jsonify({"message":"ok"}), 200


# route per visualizzare tutte le pipeline di un progetto
@bp.route('/api/v1/project/<project_id>/pipelines', methods=['GET'])
@jwt_required()
def get_all_pipeline_metabolomics(project_id):
    # prendi i dati dall'utente
    user_id = get_jwt_identity()
    result, status_code = metabolomics_views.get_all_pipeline_views(user_id, project_id)
    return jsonify(result), status_code


# route per eliminare una pipeline di un progetto
@bp.route('/api/v1/project/<project_id>/pipelines/<pipeline_id>', methods=['DELETE'])
@jwt_required()
def delete_pipeline_metabolomics(project_id, pipeline_id):
    # prendi i dati dall'utente
    user_id = get_jwt_identity()
    print(user_id, project_id, pipeline_id)
    result, status_code = metabolomics_views.delete_pipeline_views(user_id, project_id, pipeline_id)
    return jsonify(result), status_code


# metabolomics route to get the metabolomics upload in chunks of files
@bp.route('/api/v1/project/<project_id>/metabolomics_experiment/upload_chunk', methods=['POST'])
@jwt_required()
def upload_metabolomics_experiment_chunk(project_id):
    # get the user id
    user_id = get_jwt_identity()
    # get the chunk data
    chunk_data = request.get_json()
    # get the chunk number
    chunk_number = chunk_data.get("chunk_number")
    # get the chunk file
    chunk_file = chunk_data.get("chunk_file")
    # print the length of the chunk file
    print(len(chunk_file))
    return jsonify({"message": "ok"}), 200


# function to retrieve the results of the pipeline
@bp.route('/api/v1/project/<project_id>/pipelines/<pipeline_id>/results', methods=['GET'])
@jwt_required()
def get_pipeline_results(project_id, pipeline_id):
    # get the user id
    user_id = get_jwt_identity()
    # call the view function to get the results
    result, status_code = metabolomics_views.get_metabolomics_pipeline_result_views(user_id, project_id, pipeline_id)
    return jsonify(result), status_code