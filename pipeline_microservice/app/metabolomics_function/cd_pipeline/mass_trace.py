import pyopenms as oms


def run_mass_trace_detection(input_file, polarity="negative"):
    """
    This function runs the mass trace detection on the input file.
    :param input_file: The input file to be processed.
    
    :return: None   
    """
    mass_traces = []
    # load input mzml file
    exp = oms.MSExperiment()
    # load the mzML file
    oms.MzMLFile().load(input_file, exp)
    
    # Filter spectra by polarity if specified
    if polarity != "both":
        filtered_exp = oms.MSExperiment()
        target_polarity = (oms.IonSource.Polarity.NEGATIVE if polarity == "negative" 
                          else oms.IonSource.Polarity.POSITIVE)
        
        for spectrum in exp:
            if spectrum.getInstrumentSettings().getPolarity() == target_polarity:
                filtered_exp.addSpectrum(spectrum)
        
        print(f"Filtered to {polarity} mode: {filtered_exp.size()} spectra out of {exp.size()}")
        exp = filtered_exp
    
    mtd = oms.MassTraceDetection()
    # get the default parameters
    mtd_params = mtd.getDefaults()
    # adjust the parameters
     # adjust the parameters for negative mode
    if polarity == "negative":
        mtd_params.setValue("mass_error_ppm", 5.0)  # Slightly higher tolerance for negative mode
    else:
        mtd_params.setValue("mass_error_ppm", 1.0)
    mtd.setParameters(mtd_params)
    # run the mass trace detection
    mtd.run(exp, mass_traces, 0)  # 0 is the MS1
    # print the number of mass traces
    print(f"Number of mass traces: {len(mass_traces)}")
    return mass_traces
    
    
if __name__ == "__main__":
    # test the function
    input_file = "/media/datastorage/it_cast/omnis_microservice_db/test_db/file_mzml/20250228_04_03.mzML"
    run_mass_trace_detection(input_file)