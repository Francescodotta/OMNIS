import pyopenms as oms

def validate_input_parameters(params):
    """Validate all input parameters for spectrum filtering."""
    if params['lower_rt'] < 0:
        raise ValueError("Lower RT limit cannot be negative")
    if params['upper_rt'] < 0:
        raise ValueError("Upper RT limit cannot be negative")
    if params['first_scan'] < 0:
        raise ValueError("First scan number cannot be negative")
    if params['last_scan'] < 0:
        raise ValueError("Last scan number cannot be negative")
    if params['lowest_charge'] < 0:
        raise ValueError("Lowest charge state cannot be negative")
    if params['highest_charge'] < 0:
        raise ValueError("Highest charge state cannot be negative")
    if params['min_precursor_mass'] < 0:
        raise ValueError("Minimum precursor mass cannot be negative")
    if params['max_precursor_mass'] < 0:
        raise ValueError("Maximum precursor mass cannot be negative")
    if params['minimum_peak_count'] < 1:
        raise ValueError("Minimum peak count must be at least 1")

def process_ignore_scans(ignore_scans):
    """Process the ignore_scans parameter and return a set of scan numbers to ignore."""
    ignored_scan_numbers = set()
    if ignore_scans:
        for scan_entry in ignore_scans:
            if isinstance(scan_entry, str) and '-' in scan_entry:
                start, end = map(int, scan_entry.split('-'))
                ignored_scan_numbers.update(range(start, end + 1))
            else:
                ignored_scan_numbers.add(int(scan_entry))
    return ignored_scan_numbers

def check_scan_filters(spectrum, params, ignored_scan_numbers, stats):
    """Check scan number related filters."""
    scan_number = spectrum.getNativeID()
    
    if scan_number in ignored_scan_numbers:
        stats['ignored_scans'] += 1
        return False
    
    if params['first_scan'] > 0 and scan_number < params['first_scan']:
        stats['scan_filtered'] += 1
        return False
        
    if params['last_scan'] > 0 and scan_number > params['last_scan']:
        stats['scan_filtered'] += 1
        return False
    
    return True

def check_rt_filters(spectrum, params, stats):
    """Check retention time filters."""
    rt = spectrum.getRT()
    
    if params['lower_rt'] > 0 and rt < params['lower_rt']:
        stats['rt_filtered'] += 1
        return False
        
    if params['upper_rt'] > 0 and rt > params['upper_rt']:
        stats['rt_filtered'] += 1
        return False
    
    return True

def check_charge_and_mass_filters(spectrum, params, stats):
    """Check charge state and precursor mass filters for MS2+ spectra."""
    if spectrum.getMSLevel() > 1:
        precursors = spectrum.getPrecursors()
        if precursors:
            charge = precursors[0].getCharge()
            # Check charge state
            if ((params['lowest_charge'] > 0 and charge < params['lowest_charge']) or 
                (params['highest_charge'] > 0 and charge > params['highest_charge'])):
                stats['charge_filtered'] += 1
                return False
            
            # Check precursor mass
            mz = precursors[0].getMZ()
            if charge > 0:
                mass = (mz * charge) - (charge * 1.007276)  # Convert to neutral mass
                if ((params['min_precursor_mass'] > 0 and mass < params['min_precursor_mass']) or 
                    (params['max_precursor_mass'] > 0 and mass > params['max_precursor_mass'])):
                    stats['mass_filtered'] += 1
                    return False
    return True

def check_intensity_and_peak_filters(spectrum, params, stats):
    """Check intensity and peak count filters."""
    # Check total intensity
    total_intensity = sum(spectrum.get_peaks()[1])
    if total_intensity < params['total_intensity_threshold']:
        stats['intensity_filtered'] += 1
        return False
    
    # Check peak count
    if len(spectrum.get_peaks()[0]) < params['minimum_peak_count']:
        stats['peak_count_filtered'] += 1
        return False
    
    return True

def print_filter_summary_spectrum_properties(stats, filtered_spectra):
    """Print summary of filtering results."""
    print("\nFiltering Summary:")
    print(f"Total spectra: {stats['total']}")
    print(f"Retained spectra: {len(filtered_spectra)}")
    print("\nSpectra removed by filter:")
    print(f"Retention time: {stats['rt_filtered']}")
    print(f"Scan range: {stats['scan_filtered']}")
    print(f"Ignored scans: {stats['ignored_scans']}")
    print(f"Charge state: {stats['charge_filtered']}")
    print(f"Intensity threshold: {stats['intensity_filtered']}")
    print(f"Peak count: {stats['peak_count_filtered']}")
    
    
    
def spectrum_properties_filter(spectra,
                             lower_rt=0.0,
                             upper_rt=0.0,
                             first_scan=0,
                             last_scan=0,
                             ignore_scans=None,
                             lowest_charge=0,
                             highest_charge=0,
                             min_precursor_mass=0.0,
                             max_precursor_mass=0.0,
                             total_intensity_threshold=0.0,
                             minimum_peak_count=1):
    """
    Main function for Spectrum Properties Filter.
    Filters spectra based on various properties.
    """
    # Create parameters dictionary
    params = locals()
    del params['spectra']  # Remove spectra from params dict
    
    # Validate input parameters
    validate_input_parameters(params)
    
    # Process ignore_scans parameter
    ignored_scan_numbers = process_ignore_scans(ignore_scans)
    
    # Initialize statistics
    stats = {
        'total': len(spectra),
        'rt_filtered': 0,
        'scan_filtered': 0,
        'charge_filtered': 0,
        'mass_filtered': 0,
        'intensity_filtered': 0,
        'peak_count_filtered': 0,
        'ignored_scans': 0
    }
    
    # Print initial settings
    print("\nSpectrum Properties Filter")
    print("=========================")
    print(f"RT range: {lower_rt}-{upper_rt if upper_rt > 0 else 'end'} min")
    print(f"Scan range: {first_scan}-{last_scan if last_scan > 0 else 'end'}")
    print(f"Charge state range: {lowest_charge}-{highest_charge if highest_charge > 0 else 'unlimited'}")
    if max_precursor_mass != 0:
        print(f"Precursor mass range: {min_precursor_mass}-{max_precursor_mass if max_precursor_mass > 0 else 'unlimited'} Da")
    
    # Filter spectra
    filtered_spectra = []
    for spectrum in spectra:
        # Apply all filters
        if not check_scan_filters(spectrum, params, ignored_scan_numbers, stats):
            continue
        if not check_rt_filters(spectrum, params, stats):
            continue
        if not check_charge_and_mass_filters(spectrum, params, stats):
            continue
        if not check_intensity_and_peak_filters(spectrum, params, stats):
            continue
        
        # If all filters passed, keep the spectrum
        filtered_spectra.append(spectrum)
    
    # Print summary
    print_filter_summary_spectrum_properties(stats, filtered_spectra)
    
    return filtered_spectra