from flask import Blueprint, jsonify, request
from app.tasks import flow_cytometry_unserialized, run_metabolomics_pipeline_task
bp = Blueprint('tasks', __name__)


@bp.route('/api/process_flow_cytometry', methods=['POST'])
def run_flow_cytometry():
    data = request.get_json()
    print(data) 
    
    try:
        # Creazione della catena e avvio della pipeline
        result = flow_cytometry_unserialized.delay(data)
        
        # Restituisci l'ID della catena per monitoraggio
        return jsonify({"chain_id": result.id}), 202

    except Exception as e:
        print(e)    
        return jsonify({"error": str(e)}), 400
    
@bp.route('/api/v1/process_metabolomics_pipeline', methods=['POST'])
def run_metabolomics_pipeline():
    data = request.get_json()
    #debug statement
    print(data)
    try:
        # Call the task asynchronously with .delay()
        result = run_metabolomics_pipeline_task.delay(data)
        
        return jsonify({'chain_id': result.id}), 202
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 400
