import pyopenms
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()


## create a basic function to run the correct msfragger

def msfragger_node(spectra_file, msfragger_path, params_file, java_path="/usr/local/jdk-11.0.26+4/bin/java", memory="16G"):
    """
    Function to run MSFragger on a given mzML file.
    Parameters:
        msfragger_path (str): Path to the MSFragger JAR file.
        params_file (str): Path to the MSFragger parameters file.
        java_path (str): Path to the Java executable.
        memory (str): Memory allocation for Java (e.g., "16G").
    """
    
    # check the java version
    java_version_command = [java_path, "-version"]
    java_version_process = subprocess.run(java_version_command, capture_output=True, text=True)
    # add a debugging output defining the file processing
    
    # run ms fragger with the specified java version
    command = [java_path, "-Xmx" + memory, "-jar", msfragger_path, params_file, spectra_file]
    
    # get the result of the msfragger process
    result = subprocess.run(command, capture_output=True, text=True)
    
    # output the result of the msfragger process
    if result.returncode == 0:
        print(f"Successfully processed: {spectra_file}")
    else:
        print(f"Error processing {spectra_file}: {result.stderr}")
        
    # return the path of the processed msfragger file 
    return spectra_file.replace(".mzML", ".pin")





# test the function
if __name__ == "__main__":
    # get the base path of the tools
    base_path = os.getenv("TOOLS_BASE_PATH")
    
    # define the parameters
    spectra_file = "/media/datastorage/it_cast/omnis_microservice_db/test_db/20250228_04_01.mzML"
    msfragger_path = os.path.join(base_path, "MSFragger.jar")
    params_file = os.path.join(base_path, "parameters", "fragger.params")
    
    # run the function
    msfragger_node(spectra_file, msfragger_path, params_file)