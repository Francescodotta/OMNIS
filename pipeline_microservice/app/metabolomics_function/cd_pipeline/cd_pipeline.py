import pyopenms
from mass_trace import run_mass_trace_detection 
from elution_peak import run_elution_peak_detection
from feature_map import run_feature_mapping


def run_cd_pipeline(mzml_files):
    """
    This function runs the complete CD pipeline on the input mzML files.
    :param mzml_files: The input mzML files to be processed.
    
    :return: A dictionary containing the results of the CD pipeline.
    """
    # Initialize an empty dictionary to store the results
    results = {}
    
    # Iterate over each mzML file
    for mzml_file in mzml_files:
        # Run mass trace detection
        mass_traces = run_mass_trace_detection(mzml_file)
        results[mzml_file] = {
            "mass_traces": mass_traces,
            "elution_peaks": None,
            "features": None
        }
        
        # Run elution peak detection
        mass_traces_split = run_elution_peak_detection(mass_traces)
        results[mzml_file]["elution_peaks"] = mass_traces_split
        
        # Run feature map detection
        features = run_feature_mapping(mzml_file, mass_traces_split)
        results[mzml_file]["features"] = features
    
    return results


if __name__ == "__main__":
    # Test the function with a sample mzML file
    mzml_files = ["/media/datastorage/it_cast/omnis_microservice_db/test_db/20250228_04_03.mzML"]
    results = run_cd_pipeline(mzml_files)
    
    # Print the results
    for mzml_file, result in results.items():
        print(f"Results for {mzml_file}:")
        print(f"Mass Traces: {result['mass_traces']}")
        print(f"Elution Peaks: {result['elution_peaks']}")
        print(f"Features: {result['features']}")
    