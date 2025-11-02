from app.metabolomics_function.select_spectra import main
import redis
from app import celery_microservice

@celery_microservice.task(name = "app.pipeline_task.metabolomics.select_spectra")
def select_spectra_metabolomics (serialized_experiments, parameters):
    # empty list to store the filtered experiments
    filtered_exp = []
    ## iterate over the experiments
    for json_exp in serialized_experiments:
        # logic to extrapolate from the parameters the scan and spectrum params
        scan_event_params = []
        spectrum_properties_params = []
        ## perform the main function to each experiment
        # check if the params are empty lists: 
        if len(scan_event_params) == 0 and len(spectrum_properties_params) == 0:
            
            json_exp = main.select_spectra_main(json_exp)
        filtered_exp.append(json_exp)
    return filtered_exp


