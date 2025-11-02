import pyopenms as oms
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

METABOLOMICS_SAVE_PATH = os.getenv("METABOLOMICS_BASE_PATH")

def run_feature_mapping(filename, mass_traces_split, polarity='negative'):
    """
    This function runs the feature mapping on the input file.
    :param filename: The mzML file path (without extension).
    :param mass_traces_split: The input mass traces to be processed.
    :param polarity: Ionization polarity ('positive' or 'negative').
    :return: FeatureMap object
    """
    # FEATURE MAPPING
    feature_map = oms.FeatureMap()
    feature_chromatograms = []
    ffm = oms.FeatureFindingMetabo()
    ffm_params = ffm.getDefaults()
    
    # Set stricter parameters to reduce false positives
    ffm_params.setValue("local_rt_range", 8.0)  # Narrow RT range for coeluting traces (default 10.0)
    ffm_params.setValue("local_mz_range", 5.0)  # Narrow m/z range for isotopic traces (default 6.5)
    ffm_params.setValue("charge_lower_bound", 1)  # Positive charges for positive mode
    ffm_params.setValue("charge_upper_bound", 3)
    ffm_params.setValue("chrom_fwhm", 5.0)  # Narrower expected peak width (default 5.0)
    ffm_params.setValue("isotope_filtering_model", "metabolites (5% RMS)")  # Stricter isotope model (default "metabolites (5% RMS)")
    ffm_params.setValue("remove_single_traces", "false")  # Remove unassembled traces to reduce noise (default "false")
    ffm_params.setValue("mz_scoring_by_elements", "false")  # Use element-based m/z scoring (default "false")
    ffm_params.setValue("elements", "CHNOPS")  # Keep default elements
    # Other defaults like enable_RT_filtering=true, use_smoothed_intensities=true are kept
    
    ffm.setParameters(ffm_params)
    ffm.run(mass_traces_split, feature_map, feature_chromatograms)
    print(f"Number of features after feature mapping: {feature_map.size()}")

    # Set the spectra_data meta value for downstream compatibility
    mzml_basename = os.path.basename(filename) + ".mzML"
    feature_map.setMetaValue("spectra_data", [mzml_basename.encode()])

    # Store the feature map in xml file
    filename = os.path.basename(filename)
    # remove the extension
    filename = os.path.splitext(filename)[0]
    print(f"Saving feature map to {filename}_feature_map.featureXML")
    output_file = os.path.join(METABOLOMICS_SAVE_PATH, f"{filename}_feature_map.featureXML")
    oms.FeatureXMLFile().store(output_file, feature_map)
    print(f"Feature map saved to {output_file}")
    return output_file

if __name__ == "__main__": 
    from mass_trace import run_mass_trace_detection
    from elution_peak import run_elution_peak_detection
    # test the function
    input_file = "/media/datastorage/it_cast/omnis_microservice_db/metabolomics/20231006_NA_01.mzML"
    mass_traces = run_mass_trace_detection(input_file, polarity='negative')
    mass_traces_split = run_elution_peak_detection(mass_traces)
    run_feature_mapping("/media/datastorage/it_cast/omnis_microservice_db/test_db/20231006_NA_01", mass_traces_split, polarity='negative')