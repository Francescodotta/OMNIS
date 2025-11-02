import os 
import pyopenms as oms
from app import celery_microservice
from ..proteomics_functions import processing_workflow as pw
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

proteomics_save_path = os.getenv('PROTEOMICS_SAVE_PATH')

# function for the select mzml files
@celery_microservice.task(name='app.pipeline_tasks.proteomics.select_mzml_files')
def select_mzml_files(file_paths: list):
    """
    Celery task to select mzML files from a list of file paths.
    
    Args:
        file_paths (list): List of paths to mzML files.
        
    Returns:
        list: List of selected mzML files.
    """
    try:
        # iterate over files
        saved_files = []

        # create a directory to store the files generated in the pipeline
        if not os.path.exists('generated_files'):
            os.makedirs('generated_files')

        for file_path in file_paths:
            # check if the file is mzML
            if file_path.endswith('.mzML'):
                # save the file to the list
                saved_files.append(file_path)
        # return the list of mzML files
        return saved_files
    except Exception as e:
        print(f"Error in select_mzml_files_task: {str(e)}")
        raise e


@celery_microservice.task(name='app.pipeline_tasks.proteomics.select_spectra')
def select_spectra(file_paths, lower_rt=None, upper_rt=None, first_scan=None, last_scan=None):
    """
    Celery task to select spectra from mzML files based on retention time or scan range.
    
    Args:
        file_paths (list): List of paths to mzML files.
        lower_rt (float): Lower bound of the RT range in seconds.
        upper_rt (float): Upper bound of the RT range in seconds.
        first_scan (int): First scan number.
        last_scan (int): Last scan number.
        
    Returns:
        list: List of selected spectra.
    """
    try:
        # use the output of the select_mzml_files task
        # iterate over files
        saved_files_filtered = []
        for file_path in file_paths:
            # check the rt 
            if lower_rt is not None and upper_rt is not None:
                selected_spectra = pw.select_spectra_by_rt(file_path, lower_rt, upper_rt)
            # if only one 
            # check the scan
            elif first_scan is not None or last_scan is not None:
                selected_spectra = pw.select_spectra_by_scan(file_path, first_scan, last_scan)
            # save the spectra to the file
            # create a file name to save the spectra
            file_name = os.path.basename(file_path) + "_filtered.mzML"
            pw.save_selected_spectra(file_path, selected_spectra, file_name)
            # append the file name to the list
            saved_files_filtered.append(file_name)
        # return the list of filtered files
        return saved_files_filtered
    except Exception as e:
        print(f"Error in select_spectra_task: {str(e)}")
        raise e
    
# create the msfragger step
@celery_microservice.task(name='app.pipeline_tasks.proteomics.msfragger_step')
def msfragger_step(file_paths, params):
    """
    Celery task to run MSFragger on mzML files.
    
    Args:
        file_paths (list): List of paths to mzML files.
        params (dict): Parameters for MSFragger.
        
    Returns:
        list: List of paths to the output files.
    """
    try:
        # iterate over files
        saved_files = []
        for file_path in file_paths:
            # run msfragger
            output_file = pw.run_msfragger(file_path, params)
            # append the file name to the list
            saved_files.append(output_file)
        # return the list of output files
        return saved_files
    except Exception as e:
        print(f"Error in msfragger_step_task: {str(e)}")
        raise e