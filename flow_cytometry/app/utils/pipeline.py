import requests
from app.models.flow_cytometry import FlowCytoPipeline, ProjectModel, FlowCytoPipelineRun
import json

# function to save the pipeline inside the database
def save_flow_cytometry_pipeline_views(user, project_id, pipeline_data, status="processing"):
    # check that the project exists
    project = ProjectModel.find_by_project_id(project_id)
    
    if project is None:
        return {"error": "The project does not exist"}, 404
    
    data = json.loads(pipeline_data)
    
    pipeline = data["pipeline"]
    pipeline_name = data["name"]
    
    # if the pipeline name is missing return an error
    if not pipeline_name:
        return {"error": "Pipeline name is missing"}, 400
    
    pipeline_data_dict = {
        "project_id": project_id,
        "name": pipeline_name,  # Add the general pipeline name
        "pipeline": {
            "steps": []  # Initialize the steps list
        },
        "status": status  # Set the initial status of the pipeline
    }

    # Populate the steps according to the incoming pipeline data
    for function in pipeline:
        function_name = function["type"]
        # Append the step to the pipeline structure
        pipeline_data_dict["pipeline"]["steps"].append({
            "name": function_name,
            "parameters": function["data"]["parameters"]
        })

    # salva la pipeline nel db
    FlowCytoPipeline.create_pipeline_data(pipeline_data_dict)
    
    return {"message": f"The pipeline '{pipeline_name}' is saved in the DB"}, 200


# function to save the running pipeline in the DB
def save_flow_cytometry_pipeline_run_views(user, project_id, pipeline_data):
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    
    
    if project is None:
        return {"error": "The project does not exist"}, 404

    # save the pipeline data into db
    FlowCytoPipelineRun.create_pipeline_run_data(pipeline_data)
    
    
    return {"message": f"The pipeline run is saved in the DB"}, 200   




def send_pipeline_to_processor(pipeline_data):
    """
    Send the pipeline data to the pipeline processor service running on port 5002
    """
    try:
        # Construct the URL for the pipeline processor service
        pipeline_processor_url = "http://localhost:5002/api/process_flow_cytometry"
        
        # Send POST request to the pipeline processor
        response = requests.post(
            pipeline_processor_url,
            json=pipeline_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check if the request was successful
        if response.status_code == 202:
            return json.loads(response.text), "Pipeline sent successfully"
        else:
            return False, f"Failed to send pipeline: {response.text}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Error sending pipeline to processor: {str(e)}"
