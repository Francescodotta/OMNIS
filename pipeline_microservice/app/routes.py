from flask import Blueprint, jsonify, request
from app.tasks import create_pipeline_chain, create_flow_cytometry_pipeline_chain, run_proteomics_pipeline, run_metabolomics_pipeline_task

bp = Blueprint('tasks', __name__)


@bp.route('/api/process_pipeline', methods=['POST'])
def run_pipeline():
    data = request.get_json()
    print(data) 

    try:
        # Creazione della catena e avvio della pipeline
        pipeline_chain = create_pipeline_chain(data)
        result = pipeline_chain.apply_async()

        # Restituisci l'ID della catena per monitoraggio
        return jsonify({"chain_id": result.id}), 202

    except Exception as e:
        print(e)    
        return jsonify({"error": str(e)}), 400

# workflow per la citofluorimetria
@bp.route('/api/process_flow_cytometry', methods=['POST'])
def run_flow_cytometry():
    data = request.get_json()
    print(data) 
    
    try:
        # Creazione della catena e avvio della pipeline
        pipeline_chain = create_flow_cytometry_pipeline_chain(data)
        result = pipeline_chain.apply_async()

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


# route to check the status of a task
@bp.route('/api/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    from .tasks import celery_app
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)  # this is the exception raised
        }
    
    return jsonify(response)