from app.metabolomics_function.select_spectra import scan_event_filter, spectrum_properties_filter

def select_spectra_main(spectra, scan_event_params={}, spectrum_params={}):
    """
    Main function to select spectra by applying both scan event filtering and spectrum properties filtering.
    
    Args:
        spectra (list): List of MSSpectrum objects to be filtered.
        scan_event_params (dict): Parameters for the scan event filter.
        spectrum_params (dict): Parameters for the spectrum properties filter.
    
    Returns:
        list: Filtered spectra after applying both filters.
    """
    # Apply scan event filter
    filtered_spectra = scan_event_filter(spectra, **scan_event_params)
    
    # Apply spectrum properties filter
    filtered_spectra = spectrum_properties_filter(filtered_spectra, **spectrum_params)
    
    return filtered_spectra