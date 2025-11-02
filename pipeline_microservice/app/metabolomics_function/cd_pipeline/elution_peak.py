import pyopenms as oms

def run_elution_peak_detection(mass_traces):
    """
    This function runs the elution peak detection on the input file.
    :param mass_traces: The input mass traces to be processed.

    :return: None
    """
        # ELUITION PEAK DETECTION
    mass_traces_split =[]
    epd = oms.ElutionPeakDetection()
    # get the default parameters of this operation
    epd_params = epd.getDefaults()
    epd.setParameters(epd_params)
    ## personalize the parameters in a following implementation
    epd.detectPeaks(mass_traces, mass_traces_split)

    print(f"Number of mass traces after elution peak detection: {len(mass_traces_split)}")
    return mass_traces_split


if __name__ == "__main__":
    from mass_trace import run_mass_trace_detection
    # test the function
    input_file = "/media/datastorage/it_cast/omnis_microservice_db/test_db/file_mzml/20250228_04_03.mzML"
    mass_traces = run_mass_trace_detection(input_file)
    run_elution_peak_detection(mass_traces)