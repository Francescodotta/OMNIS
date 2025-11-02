import os 
import pyopenms as oms 
import subprocess
from load_dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# get the proteomics save path from the environment variable
proteomics_save_path = os.getenv('PROTEOMICS_SAVE_PATH')

def select_spectra_by_rt(mzml_file, lower_rt, upper_rt):
    """
    Selects spectra from an mzML file based on retention time (RT) range.
    
    Parameters:
        mzml_file (str): Path to the mzML file.
        lower_rt (float): Lower bound of the RT range in seconds.
        upper_rt (float): Upper bound of the RT range in seconds.
    
    Returns:
        list: List of selected spectra.
    """
    # Load the mzML file
    exp = oms.MSExperiment()
    oms.FileHandler().loadExperiment(mzml_file, exp)

    # print original len of the spectra
    print(f"Original number of spectra: {len(exp.getSpectra())}")
    
    # Select spectra based on RT range
    selected_spectra = []
    for spectrum in exp.getSpectra():
        rt = spectrum.getRT()  # Get retention time in seconds
        if lower_rt <= rt <= upper_rt:
            selected_spectra.append(spectrum)

    return selected_spectra


def select_spectra_by_scan(mzml_file, first_scan=None, last_scan=None):
    # if all the three parameters are None, return all the spectra
    if first_scan is None and last_scan is None:
        return None
    # Load the mzML file
    exp = oms.MSExperiment()
    oms.FileHandler().loadExperiment(mzml_file, exp)
    # print original len of the spectra
    print(f"Original number of spectra: {len(exp.getSpectra())}")

    # if both are true
    if first_scan is not None and last_scan is not None:
        # Select spectra based on scan range
        selected_spectra = []
        for spectrum in exp.getSpectra():
            scan = spectrum.getNativeID()
            if first_scan <= scan <= last_scan:
                selected_spectra.append(spectrum)
    # if first_scan is None, select all the spectra with scan less than last_scan
    elif first_scan is None and last_scan is not None:
        selected_spectra = []
        for spectrum in exp.getSpectra():
            scan = spectrum.getNativeID()
            if scan <= last_scan:
                selected_spectra.append(spectrum)
    # if last_scan is None, select all the spectra with scan greater than first_scan
    elif first_scan is not None and last_scan is None:
        selected_spectra = []
        for spectrum in exp.getSpectra():
            scan = spectrum.getNativeID()
            if scan >= first_scan:
                selected_spectra.append(spectrum)
    # print the number of selected spectra
    print(f"Number of selected spectra: {len(selected_spectra)}")
    return selected_spectra

def select_spectra_by_scan_range(mzml_file, scan_list):
    # function to ignore all the scans inside the list
    # Load the mzML file
    exp = oms.MSExperiment()
    oms.FileHandler().loadExperiment(mzml_file, exp)
    # print original len of the spectra
    print(f"Original number of spectra: {len(exp.getSpectra())}")
    # Select spectra based on scan range
    selected_spectra = []
    for spectrum in exp.getSpectra():
        scan = spectrum.getNativeID()
        if scan not in scan_list:
            selected_spectra.append(spectrum)
    # print the number of selected spectra
    print(f"Number of selected spectra: {len(selected_spectra)}")
    return selected_spectra

# selet spectra ased on lower charge state and higher charge state
def select_spectra_by_charge(mzml_file, lower_charge, upper_charge):
    """
    Description:
    Selects spectra from an mzML file based on charge state range. Filters out spectra with a precursor charge lower/higher than the specified charge.
    
    Parameters:
        mzml_file (str): Path to the mzML file.
        lower_charge (int): Lower bound of the charge state range.
        upper_charge (int): Upper bound of the charge state range.
    
    Returns:
        list: List of selected spectra.
    """

    exp = oms.MSExperiment()
    oms.FileHandler().loadExperiment(mzml_file, exp)
    

    selected_spectra = []
    for spectrum in exp.getSpectra():
        charge = spectrum.getCharge()
        if lower_charge <= charge <= upper_charge:
            selected_spectra.append(spectrum)
    

    print(f"Number of selected spectra: {len(selected_spectra)}")
    return selected_spectra

# select spectra based on the precursor mass
def select_spectra_by_precursor_mass(mzml_file, min_precursor_mass, max_precursor_mass):
    """
    Description:
    Selects spectra from an mzML file based on precursor mass range. Filters out spectra with a precursor mass lower/higher than the specified mass.
    
    Parameters:
        mzml_file (str): Path to the mzML file.
        min_precursor_mass (float): Lower bound of the precursor mass range.
        max_precursor_mass (float): Upper bound of the precursor mass range.
    
    Returns:
        list: List of selected spectra.
    """
    exp = oms.MSExperiment()
    oms.FileHandler().loadExperiment(mzml_file, exp)
    

    selected_spectra = []
    for spectrum in exp.getSpectra():
        precursor_mass = spectrum.getPrecursors()[0].getMZ()
        if min_precursor_mass <= precursor_mass <= max_precursor_mass:
            selected_spectra.append(spectrum)
    

    print(f"Number of selected spectra: {len(selected_spectra)}")
    return selected_spectra

def save_selected_spectra(original_file, selected_spectra, output_file):
    """
    Saves the selected spectra to a new mzML file.
    """
    # Create and load original experiment
    original_exp = oms.MSExperiment()
    mzml = oms.MzMLFile()
    mzml.load(original_file, original_exp)
    
    # modify the spectra of the original file to the selected spectra and then save the file with a new name
    exp = oms.MSExperiment()
    for spectrum in selected_spectra:
        # Copy the spectrum to the new experiment
        new_spectrum = oms.MSSpectrum()
        new_spectrum = spectrum
        exp.addSpectrum(new_spectrum)
    # Add the chromatograms from the original experiment
    for chromatogram in original_exp.getChromatograms():
        exp.addChromatogram(chromatogram)
        
    # Set the metadata of the new experiment
    exp.setSample(original_exp.getSample())
    exp.setInstrument(original_exp.getInstrument())
    
    
    
    # Store the experiment
    mzml_out = oms.MzMLFile()
    mzml_out.store(output_file, exp)



# function to perform the MSFragger workflow
def run_msfragger(
    spectra_file,
    output_dir,
    msfragger_path,
    params_file,
    fasta_files,
    java_path,
    memory,
    enzyme="trypsin",
    min_pep_length=7,
    max_pep_length=30,
    precursor_mass_tolerance=20.0,
    fragment_mass_tolerance=20.0,
    output_format="pepXML",
):
    """
    Define the parameters for the MSFragger workflow.
    
    Parameters:
        spectra_file (str): Path to the mzML file.
        output_dir (str): Directory to save the output files.
        msfragger_path (str): Path to the MSFragger jar file.
        params_file (str): Path to the MSFragger parameters file.
        java_path (str): Path to the Java executable.
        memory (str): Memory allocation for Java (e.g., "4G").
        enzyme (str): Enzyme used for digestion. Default is "trypsin".
        min_pep_length (int): Minimum peptide length. Default is 7.
        max_pep_length (int): Maximum peptide length. Default is 30.
        precursor_mass_tolerance (float): Precursor mass tolerance in ppm. Default is 20.0.
        fragment_mass_tolerance (float): Fragment mass tolerance in ppm. Default is 20.0.
        output_format (str): Output format for MSFragger. Default is "pepXML".
    
    Returns:
        None
    """
    # Check if the output directory exists, if not create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Check if the spectra file exists
    if not os.path.exists(spectra_file):
        raise FileNotFoundError(f"The spectra file {spectra_file} does not exist.")
    
    # Check if the MSFragger jar file exists
    if not os.path.exists(msfragger_path):
        raise FileNotFoundError(f"The MSFragger jar file {msfragger_path} does not exist.")
    
    # Check if the Java executable exists
    if not os.path.exists(java_path):
        raise FileNotFoundError(f"The Java executable {java_path} does not exist.")
    
    # create the param file based on the input 
    with open(params_file, "w") as f:
        f.write(f"database_name = {':'.join(fasta_files)}\n")
        f.write(f"search_enzyme_name_1 = {enzyme}\n")
        f.write(f"num_enzyme_termini = 2\n")
        f.write(f"allowed_missed_cleavage = 2\n")
        f.write(f"min_peptide_length = {min_pep_length}\n")
        f.write(f"max_peptide_length = {max_pep_length}\n")
        f.write(f"precursor_mass_tolerance = {precursor_mass_tolerance}\n")
        f.write(f"fragment_mass_tolerance = {fragment_mass_tolerance}\n")
        f.write(f"output_format = {output_format}\n")
    
    command = [
        java_path, f"-Xmx{memory}", "-jar", msfragger_path, params_file, spectra_file
    ]

    print(f"Running MSFragger with command: {' '.join(command)}")
    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode == 0:
        print(f"MSFragger completed successfully. Output files are saved in {output_dir}.")
    else:
        print(f"MSFragger failed with error: {process.stderr}")
    
    # return the path of the file which is the path of the file mzML, with changed into the output_dir
    msfragger_file_path = spectra_file.replace("mzML", output_format)
    return msfragger_file_path