import requests 



def send_pipeline_to_processor(pipeline_data):
    """
    Send the pipeline data to the pipeline processor service running on port 5002.
    Tries localhost first, then the Docker service name.
    """
    urls = [
        "http://localhost:5002/api/v1/process_metabolomics_pipeline",
        "http://pipeline_microservice:5002/api/v1/process_metabolomics_pipeline"
    ]
    for pipeline_processor_url in urls:
        try:
            response = requests.post(
                pipeline_processor_url,
                json=pipeline_data,
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code == 202:
                task_id = response.json().get('chain_id')
                if not task_id:
                    return False, "No task ID returned from the processor"
                return True, task_id
            else:
                # Try next URL if not successful
                continue
        except requests.exceptions.RequestException:
            continue
    return False, "Failed to send pipeline: All endpoints unreachable or returned an error"

