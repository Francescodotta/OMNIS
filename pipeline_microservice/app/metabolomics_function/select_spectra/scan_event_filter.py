import pyopenms as oms 

def validate_scan_event_parameters(params):
    """Validate input parameters for scan event filtering."""
    if params['min_collision_energy'] < 0:
        raise ValueError("Minimum collision energy cannot be negative")
    if params['max_collision_energy'] > 1000:
        raise ValueError("Maximum collision energy cannot exceed 1000")
    if params['max_collision_energy'] < params['min_collision_energy']:
        raise ValueError("Maximum collision energy must be greater than minimum")

def parse_mass_range(mass_range_str):
    """Parse MS1 mass range string into min and max values."""
    if not mass_range_str:
        return None, None
    try:
        mass_min, mass_max = map(float, mass_range_str.strip('[]').split('-'))
        return mass_min, mass_max
    except:
        raise ValueError("Invalid mass range format. Expected format: [min-max]")

def check_mass_analyzer(spectrum, params):
    """Check if spectrum matches mass analyzer criteria."""
    # Use the documented method getAnalyzerType() on the InstrumentSettings!
    inst_settings = spectrum.getInstrumentSettings()
    try:
        analyzer_type = str(inst_settings.getMetaValue("analyzer")) # New: use getAnalyzerType() instead of getAnalyzer()
    except AttributeError:
        print("Error: InstrumentSettings does not have getAnalyzerType()")
        return False

    # If we are not filtering by mass analyzer, allow all spectra.
    if params['mass_analyzer_filter'] == 'Any' or not params['mass_analyzers']:
        return True

    # Map common names to their standard codes.
    analyzers_map = {
        'Ion Trap': 'ITMS',
        'Fourier Transform': 'FTMS',
        'Time of Flight': 'TOFMS',
        'Single Quad': 'SQMS',
        'Triple Quad': 'TSMS',
        'Sector Field': 'SectorMS'
    }

    # Convert the preferred analyzers (from user input) into their codes.
    preferred_analyzers = [analyzers_map.get(a, a) for a in params['mass_analyzers']]

    matches = analyzer_type in preferred_analyzers
    if params['mass_analyzer_filter'] == 'Is':
        return matches
    elif params['mass_analyzer_filter'] == 'Is Not':
        return not matches
    else:
        return True

def check_activation(spectrum, params):
    """Check if spectrum matches activation criteria."""
    if params['activation_filter'] == 'Any':
        return True
    
    if spectrum.getMSLevel() == 1:
        return True
    
    activation = spectrum.getPrecursors()[0].getActivationMethod()
    activation_map = {
        'CID': 'Collision Induced Dissociation',
        'MPD': 'Multi Photon Dissociation',
        'ECD': 'Electron Capture Dissociation',
        'PQD': 'Pulsed Q Collision Induced Dissociation',
        'ETD': 'Electron Transfer Dissociation',
        'HCD': 'Higher Energy Collision Dissociation',
        'EThcD': 'ETD With Supplemental HCD',
        'UVPD': 'Ultra Violet Photon Dissociation'
    }
    
    matches = activation in [activation_map[a] for a in params['activation_types']]
    return matches if params['activation_filter'] == 'Is' else not matches

def check_collision_energy(spectrum, params):
    """Check if spectrum matches collision energy criteria."""
    if spectrum.getMSLevel() == 1:
        return True
    
    collision_energy = spectrum.getPrecursors()[0].getActivationEnergy()
    return (params['min_collision_energy'] <= collision_energy <= 
            params['max_collision_energy'])

def check_scan_type(spectrum, params):
    """Check if spectrum matches scan type criteria."""
    if params['scan_type_filter'] == 'Any':
        return True
    
    scan_type = spectrum.getInstrumentSettings().getScanType()
    scan_types_map = {
        'Full': 'FULL',
        'Selected Ion Monitoring': 'SIM',
        'Selected Reaction Monitoring': 'SRM'
    }
    
    matches = scan_type in [scan_types_map[s] for s in params['scan_types']]
    return matches if params['scan_type_filter'] == 'Is' else not matches

def check_polarity(spectrum, params):
    """
    Filters out spectra that do not respect the user-defined polarity.

    PyOpenMS returns the polarity from:
        spectrum.getInstrumentSettings().getPolarity()
    as an integer:
       "Neutral"  -> 0
       "Positive" -> 1
       "Negative" -> 2

    The user must provide a key "polarities" in the params dictionary with a list 
    of accepted polarity strings. For example, to keep only negative spectra, the user 
    should set:
    
        params = {"polarities": ["Negative"]}
    
    In that case, the function will only allow spectra whose polarity value is 2.
    
    Args:
        spectrum (MSSpectrum): A PyOpenMS spectrum.
        params (dict): A dictionary with filtering parameters.
            Must include "polarities": list of allowed values among "Neutral", "Positive", "Negative".
    
    Returns:
        bool: True if the spectrum's polarity value is one of the allowed values; False otherwise.
    """
    # Retrieve the allowed polarities list from parameters.
    allowed = params.get("polarities", [])
    
    # No filtering if allowed list is not provided.
    if not allowed:
        return True

    # Map allowed polarity strings to their corresponding integer codes.
    # Allowed values: "Neutral" -> 0, "Positive" -> 1, "Negative" -> 2.
    polarity_mapping = {
        "neutral": 0,
        "positive": 1,
        "negative": 2
    }
    
    allowed_codes = []
    for pol in allowed:
        key = pol.strip().lower()
        if key in polarity_mapping:
            allowed_codes.append(polarity_mapping[key])
        else:
            print(f"Warning: Unrecognized polarity '{pol}'. Allowed values are 'Neutral', 'Positive', 'Negative'.")
    
    # Retrieve the spectrum's polarity.
    # This method returns an integer (0, 1, or 2) corresponding to "Neutral", "Positive", "Negative" respectively.
    spectrum_polarity = spectrum.getInstrumentSettings().getPolarity()
    
    # Only allow the spectrum if its polarity is one of the allowed codes.
    return spectrum_polarity in allowed_codes

def check_ms1_mass_range(spectrum, params):
    """Check if MS1 spectrum matches mass range criteria."""
    if spectrum.getMSLevel() != 1 or not params['ms1_mass_range']:
        return True
    
    mass_min, mass_max = params['ms1_mass_range']
    mz_array, _ = spectrum.get_peaks()
    return all(mass_min <= mz <= mass_max for mz in mz_array)

def check_ms_order(spectrum, params):
    """Check if spectrum matches MS order criteria."""
    if params['ms_order_filter'] == 'Any':
        return True
    
    ms_level = spectrum.getMSLevel()
    matches = ms_level in params['ms_orders']
    return matches if params['ms_order_filter'] == 'Is' else not matches

def print_filter_summary(stats, filtered_spectra):
    """Print summary of filtering results."""
    print("\nScan Event Filter Summary:")
    print(f"Total spectra: {stats['total']}")
    print(f"Retained spectra: {len(filtered_spectra)}")
    print("\nSpectra removed by filter:")
    if stats['mass_analyzer_filtered'] != 0:    
        print(f"Mass analyzer: {stats['mass_analyzer_filtered']}")
    if stats['activation_filtered'] != 0:
        print(f"Activation type: {stats['activation_filtered']}")
    if stats['collision_energy_filtered'] != 0:
        print(f"Collision energy: {stats['collision_energy_filtered']}")
    print(f"Scan type: {stats['scan_type_filtered']}")
    print(f"Polarity: {stats['polarity_filtered']}")
    print(f"MS1 mass range: {stats['mass_range_filtered']}")
    print(f"MS order: {stats['ms_order_filtered']}")


def scan_event_filter(spectra,
                     # Mass Analyzer
                     mass_analyzer_filter='Any',
                     mass_analyzers=None,
                     # Activation
                     activation_filter='Any',
                     activation_types=None,
                     min_collision_energy=0,
                     max_collision_energy=1000,
                     # Scan Type
                     scan_type_filter='Any',
                     scan_types=None,
                     # Polarity
                     polarity_filter='Any',
                     polarities=None,
                     # MS1 Mass Range
                     ms1_mass_range='',
                     # MS Order
                     ms_order_filter='Any',
                     ms_orders=None):
    """
    Main function for Scan Event Filter.
    Filters spectra based on various scan event properties.
    """
    # Set defaults for optional parameters
    if mass_analyzers is None:
        mass_analyzers = ['Ion Trap', 'Fourier Transform']
    if activation_types is None:
        activation_types = ['CID', 'HCD']
    if scan_types is None:
        scan_types = ['Full']
    if polarities is None:
        polarities = ['Positive', 'Negative']
    if ms_orders is None:
        ms_orders = list(range(1, 8))  # MS1-MS7
    
    # Create parameters dictionary
    params = {
        'mass_analyzer_filter': mass_analyzer_filter,
        'mass_analyzers': mass_analyzers,
        'activation_filter': activation_filter,
        'activation_types': activation_types,
        'min_collision_energy': min_collision_energy,
        'max_collision_energy': max_collision_energy,
        'scan_type_filter': scan_type_filter,
        'scan_types': scan_types,
        'polarity_filter': polarity_filter,
        'polarities': polarities,
        'ms1_mass_range': parse_mass_range(ms1_mass_range) if ms1_mass_range else None,
        'ms_order_filter': ms_order_filter,
        'ms_orders': ms_orders
    }
    
    # Validate parameters
    validate_scan_event_parameters(params)
    
    # Initialize statistics
    stats = {
        'total': len(spectra),
        'mass_analyzer_filtered': 0,
        'activation_filtered': 0,
        'collision_energy_filtered': 0,
        'scan_type_filtered': 0,
        'polarity_filtered': 0,
        'mass_range_filtered': 0,
        'ms_order_filtered': 0
    }
    
    # Filter spectra
    filtered_spectra = []
    for spectrum in spectra:
        # Apply all filters
        if not check_mass_analyzer(spectrum, params):
            stats['mass_analyzer_filtered'] += 1
            continue
        if not check_activation(spectrum, params):
            stats['activation_filtered'] += 1
            continue
        if not check_collision_energy(spectrum, params):
            stats['collision_energy_filtered'] += 1
            continue
        if not check_scan_type(spectrum, params):
            stats['scan_type_filtered'] += 1
            continue
        if not check_polarity(spectrum, params):
            stats['polarity_filtered'] += 1
            continue
        if not check_ms1_mass_range(spectrum, params):
            stats['mass_range_filtered'] += 1
            continue
        if not check_ms_order(spectrum, params):
            stats['ms_order_filtered'] += 1
            continue
        
        filtered_spectra.append(spectrum)
    
    # Print summary
    print_filter_summary(stats, filtered_spectra)
    
    return filtered_spectra