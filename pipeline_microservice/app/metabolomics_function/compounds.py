import pandas as pd 
import numpy as np
import json
import time
import pyopenms as oms
from typing import List, Dict, Tuple
from .isotopes import IsotopeHandler
## In questo file ci sono le funzioni per detection e grouping dei composti


# Estraiamo il numero di scan dalla stringa
def extract_chromatograms_from_json(exp_json, mass_tolerance_ppm):
    if not (1 <= mass_tolerance_ppm <= 20):
        raise ValueError("Mass tolerance must be between 1 and 20 ppm")

    df = pd.read_json(exp_json)
    ms1_spectra = df[df['ms_level'] == 1]

    # Controlla se ms1_spectra è vuoto
    if ms1_spectra.empty:
        raise ValueError("No MS1 spectra found in the provided data.")

    # Controlla se le colonne necessarie esistono
    required_columns = ['mzarray', 'intarray', 'RT', 'scan_number']
    for col in required_columns:
        if col not in ms1_spectra.columns:
            raise ValueError(f"Missing required column: {col}")

    # Estrai i numeri di scansione e converti in interi
    ms1_spectra['scan_number'] = ms1_spectra['scan_number'].str.extract(r'scan=(\d+)').astype(int)

    # Crea una lista per memorizzare i cromatogrammi
    chromatograms = []

    for _, spectrum in ms1_spectra.iterrows():
        mzs = spectrum['mzarray']
        intensities = spectrum['intarray']
        rt = spectrum['RT']
        scan_number = spectrum['scan_number']

        # Assicurati che mzs e intensities siano liste
        if isinstance(mzs, list) and isinstance(intensities, list):
            for mz, intensity in zip(mzs, intensities):
                # Crea un dizionario per il cromatogramma
                chromatogram = {
                    'native_id': f"chrom_{mz}_{mass_tolerance_ppm}ppm",
                    'mz': mz,
                    'rt': rt,
                    'intensity': intensity,
                    'scans': scan_number
                }
                chromatograms.append(chromatogram)

    # Converti in DataFrame e poi in JSON
    chroms_df = pd.DataFrame(chromatograms)
    return chroms_df.to_json()

def filter_peaks_by_intensity(chromatograms_json, min_peak_intensity):
    """
    Filters peaks in chromatograms based on the minimum peak intensity.

    Parameters:
    chromatograms_json (str): JSON string representing the list of chromatograms.
    min_peak_intensity (float): The minimum peak intensity.

    Returns:
    str: JSON string of chromatograms with filtered peaks.
    """
    
    
    # Convert JSON string to DataFrame
    chromatograms_df = pd.read_json(chromatograms_json)
    print(f"Number of chromatograms before filtering: {len(chromatograms_df)}")
    
    # Filter the DataFrame directly based on intensity
    filtered_df = chromatograms_df[chromatograms_df['intensity'] >= min_peak_intensity]

    
    # Create the output format
    filtered_chromatograms = filtered_df.apply(
        lambda row: {
            'native_id': row['native_id'],
            'peaks': [{'mz': row['mz'], 'intensity': row['intensity']}],
            'rt': row['rt'],
            'scans': row['scans']
        }, 
        axis=1
    ).tolist()

    print(f"Number of chromatograms after filtering: {len(filtered_chromatograms)}")
    return pd.DataFrame(filtered_chromatograms).to_json()


def filter_chromatograms_by_scans(chromatograms_json, min_scans_per_peak):
    """
    Filters chromatograms based on the minimum number of scans per peak.

    Parameters:
    chromatograms_json (str): JSON string representing the list of chromatograms.
    min_scans_per_peak (int): The minimum number of scans per peak.

    Returns:
    str: JSON string of filtered chromatograms.
    """
    # Convert JSON string to DataFrame
    chromatograms_df = pd.read_json(chromatograms_json)
    print(chromatograms_df.head())
    print(f"Number of chromatograms before filtering: {len(chromatograms_df)}")
    # Filter chromatograms based on the minimum number of scans per peak
    filtered_df = chromatograms_df[chromatograms_df['scans'] >= float(min_scans_per_peak)]
    print(f"Number of chromatograms after filtering: {len(filtered_df)}")   
    # Convert the filtered DataFrame back to JSON
    return filtered_df.to_json()


def process_isotopes_from_json(chromatograms_json, most_intense_isotope_only):
    """
    Processes isotopes in chromatograms based on the specified parameter.

    Parameters:
    chromatograms_json (str): JSON string representing the list of chromatograms.
    most_intense_isotope_only (bool): If True, report only the most intense isotope peak. If False, sum the areas of all isotopic peaks.

    Returns:
    str: JSON string of processed chromatograms.
    """
    # Carica i cromatogrammi dal JSON usando pd.read_json
    chromatograms_df = pd.read_json(chromatograms_json)
    processed_chromatograms = []

    for _, chrom in chromatograms_df.iterrows():
        # Assicurati di accedere correttamente alle colonne
        peaks = chrom['peaks']  # Lista di picchi
        rt = chrom.get('rt', None)  # Usa get per evitare KeyError
        scan_number = chrom['scans']
        native_id = chrom['native_id']

        if most_intense_isotope_only:
            # Trova il picco con l'intensità massima
            max_intensity_peak = max(peaks, key=lambda peak: peak['intensity'])
            processed_chrom = {
                'native_id': native_id,
                'peaks': [max_intensity_peak]  # Solo il picco più intenso
            }
            if rt is not None:
                processed_chrom['rt'] = rt  # Aggiungi 'rt' se disponibile
            processed_chrom['scans'] = scan_number  # Aggiungi scans
            processed_chromatograms.append(processed_chrom)
        else:
            summed_intensity = sum(peak['intensity'] for peak in peaks)
            summed_chrom = {
                'native_id': native_id,
                'peaks': [],  # Lista per i nuovi picchi
                'rt':rt,
                'scans': scan_number
            }
            for peak in peaks:
                new_peak = {
                    'mz': peak['mz'],
                    'intensity': summed_intensity,  # Intensità totale
                }
                summed_chrom['peaks'].append(new_peak)
            processed_chromatograms.append(summed_chrom)

    # Restituisci il risultato come JSON
    return json.dumps(processed_chromatograms)



def correct_gaps_from_json(chromatograms_json, max_gaps):
    """
    Corrects gaps in chromatograms based on the specified maximum number of continuous gaps.

    Parameters:
    chromatograms_json (str or list): JSON string or list representing the list of chromatograms.
    max_gaps (int): The maximum number of continuous gaps to correct.

    Returns:
    str: JSON string of chromatograms with corrected gaps.
    """
    # Se l'input è una stringa JSON, caricalo in un DataFrame
    if isinstance(chromatograms_json, str):
        chromatograms_df = pd.read_json(chromatograms_json)
    elif isinstance(chromatograms_json, list):
        chromatograms_df = pd.DataFrame(chromatograms_json)
    else:
        raise ValueError("Input must be a JSON string or a list of dictionaries.")

    corrected_chromatograms = []
    
    #vedi il numero di cromatogrammi
    print(f"Number of chromatograms: {len(chromatograms_df)}")
    
    for _, chrom in chromatograms_df.iterrows():
        corrected_chrom = {
            'native_id': chrom['native_id'],
            'peaks': []  # Lista per i picchi corretti
        }
        
        peaks = chrom['peaks']  # Lista di picchi

        for i in range(len(peaks)):
            # Aggiungi il picco originale
            corrected_chrom['peaks'].append({
                'mz': peaks[i]['mz'],
                'intensity': peaks[i]['intensity'],
                'rt': chrom['rt'],  # Usa il valore di rt dal cromatogramma
                'scans': chrom['scans']
            })

            if i < len(peaks) - 1:
                # Calcolo della dimensione del gap
                gap_size = int((peaks[i + 1]['mz'] - peaks[i]['mz']) / (peaks[1]['mz'] - peaks[0]['mz'])) - 1
                if 0 < gap_size <= max_gaps:
                    for j in range(1, gap_size + 1):
                        new_peak = {
                            'mz': peaks[i]['mz'],  # Puoi mantenere lo stesso mz o modificarlo se necessario
                            'intensity': 0,  # Intensità zero per i picchi corretti
                            'rt': chrom['rt'],  # Usa il valore di rt dal cromatogramma
                            'scans': chrom['scans']
                        }
                        corrected_chrom['peaks'].append(new_peak)
            #print il numero di picchi corretti
        print(f"Number of corrected peaks: {len(corrected_chrom['peaks'])}")

        corrected_chromatograms.append(corrected_chrom)
    #vedi il numero di cromatogrammi
    print(f"Number of chromatograms after correction: {len(corrected_chromatograms)}")
    # Restituisci il risultato come JSON
    return json.dumps(corrected_chromatograms)



def correct_gaps_with_min_adjacent_non_zeros(chromatograms_json, max_gaps_maz, min_adjacent_non_zeros):
    """
    Corrects gaps in chromatograms based on the specified maximum number of continuous gaps
    and the minimum number of adjacent non-zero values required to correct a gap.

    Parameters:
    chromatograms_json (str or list): JSON string or list representing the list of chromatograms.
    max_gaps_maz (int): The maximum number of continuous gaps to correct.
    min_adjacent_non_zeros (int): The minimum number of adjacent non-zero values required to correct a gap.

    Returns:
    str: JSON string of chromatograms with corrected gaps.
    """
    # Se l'input è una stringa JSON, caricalo in un DataFrame
    if isinstance(chromatograms_json, str):
        chromatograms_df = pd.read_json(chromatograms_json)
    elif isinstance(chromatograms_json, list):
        chromatograms_df = pd.DataFrame(chromatograms_json)
    else:
        raise ValueError("Input must be a JSON string or a list of dictionaries.")

    corrected_chromatograms = []

    for _, chrom in chromatograms_df.iterrows():
        corrected_chrom = oms.MSChromatogram()
        corrected_chrom.setNativeID(chrom['native_id'])
        peaks = chrom['peaks']  # Lista di picchi
        for i in range(len(peaks)):
            corrected_chrom.push_back(peaks[i])
            if i < len(peaks) - 1:
                gap_size = int((peaks[i + 1]['rt'] - peaks[i]['rt']) / (peaks[1]['rt'] - peaks[0]['rt'])) - 1
                if 0 < gap_size <= max_gaps_maz:
                    # Controlla i valori non zero adiacenti
                    left_non_zeros = sum(1 for j in range(max(0, i - min_adjacent_non_zeros), i) if peaks[j]['intensity'] > 0)
                    right_non_zeros = sum(1 for j in range(i + 1, min(len(peaks), i + 1 + min_adjacent_non_zeros)) if peaks[j]['intensity'] > 0)
                    if left_non_zeros >= min_adjacent_non_zeros or right_non_zeros >= min_adjacent_non_zeros:
                        for j in range(1, gap_size + 1):
                            new_peak = oms.ChromatogramPeak()
                            new_peak.setRT(peaks[i]['rt'] + j * (peaks[1]['rt'] - peaks[0]['rt']))
                            new_peak.setIntensity(0)
                            corrected_chrom.push_back(new_peak)
        corrected_chromatograms.append(corrected_chrom)

    # Converti la lista di cromatogrammi corretti in JSON
    return json.dumps(corrected_chromatograms)


def signal_noise_threshold_detectCompounds(chromatograms_json, sn_threshold):
    """
    Exclude all peaks with a chromatographic signal-to-noise ratio below the specified threshold.

    Params:
        chromatograms_json (str or list): JSON string or list representing the list of chromatograms.
        sn_threshold (float): The signal-to-noise threshold.

    Returns:
        str: JSON string of chromatograms with peaks above the signal-to-noise threshold.
    """
    # Se l'input è una stringa JSON, caricalo in un DataFrame
    if isinstance(chromatograms_json, str):
        chromatograms_df = pd.read_json(chromatograms_json)
    elif isinstance(chromatograms_json, list):
        chromatograms_df = pd.DataFrame(chromatograms_json)
    else:
        raise ValueError("Input must be a JSON string or a list of dictionaries.")

    # Vedi il numero di cromatogrammi
    filtered_chromatograms = []

    # Itera sui cromatogrammi
    for _, chrom in chromatograms_df.iterrows():
        # Crea un dizionario per il cromatogramma filtrato
        filtered_chromatogram = {
            'native_id': chrom['native_id'],
            'peaks': []  # Lista per i picchi filtrati
        }

        # Estrai i picchi
        peaks = chrom['peaks']  # Lista di picchi
        intensities = [peak['intensity'] for peak in peaks]  # Estrai le intensità

        # Calcola la mediana delle intensità
        median_intensity = np.median(intensities)

        # Itera sui picchi
        for peak in peaks:
            # Calcola il rapporto segnale-rumore
            sn_ratio = peak['intensity'] / median_intensity if median_intensity > 0 else 0
            if sn_ratio >= sn_threshold:
                # Aggiungi il picco al dizionario del cromatogramma filtrato
                filtered_chromatogram['peaks'].append({
                    'intensity': peak['intensity'],
                    'mz': peak['mz']  # Assicurati di includere anche 'mz' se necessario
                })

        filtered_chromatograms.append(filtered_chromatogram)

    return json.dumps(filtered_chromatograms)



def remove_baseline(chromatograms_json):
    """
    Removes background noise from chromatograms.

    Parameters:
    chromatograms_json (str or list): JSON string or list representing the list of chromatograms.

    Returns:
    str: JSON string of chromatograms with background noise removed.
    """
    # Se l'input è una stringa JSON, caricalo in un DataFrame
    if isinstance(chromatograms_json, str):
        chromatograms_df = pd.read_json(chromatograms_json)
    elif isinstance(chromatograms_json, list):
        chromatograms_df = pd.DataFrame(chromatograms_json)
    else:
        raise ValueError("Input must be a JSON string or a list of dictionaries.")

    processed_chromatograms = []

    for _, chrom in chromatograms_df.iterrows():
        processed_chrom = {
            'native_id': chrom['native_id'],
            'peaks': []  # Lista per i picchi elaborati
        }

        # Calcola il rumore di fondo come la mediana delle intensità del cromatogramma
        intensities = [peak['intensity'] for peak in chrom['peaks']]

        if not intensities:
            # Salta questo cromatogramma se non ci sono intensità
            processed_chromatograms.append(processed_chrom)
            continue

        baseline_noise = np.median(intensities)

        for peak in chrom['peaks']:
            new_intensity = peak['intensity'] - baseline_noise
            new_intensity = max(new_intensity, 0)  # Assicurati che l'intensità non sia negativa
            processed_chrom['peaks'].append({
                'intensity': new_intensity,
                'mz': peak['mz']  # Assicurati di includere anche 'mz' se necessario
            })

        processed_chromatograms.append(processed_chrom)

    return json.dumps(processed_chromatograms)



def filter_by_gap_ratio(chromatograms_json, gap_ratio_threshold):
    """
    Excludes all chromatograms with a gap ratio above the specific threshold.

    Parameters:
    chromatograms_json (str or list): JSON string or list representing the list of chromatograms.
    gap_ratio_threshold (float): The gap ratio threshold.

    Returns:
    str: JSON string of chromatograms with gap ratio below the threshold.
    """
    # If the input is a JSON string, load it into a DataFrame
    if isinstance(chromatograms_json, str):
        chromatograms_df = pd.read_json(chromatograms_json)
    elif isinstance(chromatograms_json, list):
        chromatograms_df = pd.DataFrame(chromatograms_json)
    else:
        raise ValueError("Input must be a JSON string or a list of dictionaries.")

    filtered_chromatograms = []

    for _, chromatogram in chromatograms_df.iterrows():
        peaks = chromatogram.get('peaks', [])
        total_peaks = len(peaks)  # Access peaks from the DataFrame
        if total_peaks == 0:
            continue

        gap_count = sum(1 for peak in peaks if peak['intensity'] == 0)
        gap_ratio = gap_count / total_peaks

        if gap_ratio <= gap_ratio_threshold:
            filtered_chromatograms.append(chromatogram)

    return json.dumps(filtered_chromatograms)



def filter_by_max_peak_width(chromatograms_json, max_peak_width):
    """
    Excludes all peaks with a peak width at half height greater than the specified maximum peak width.

    Parameters:
    chromatograms_json (str or list): JSON string or list representing the list of chromatograms.
    max_peak_width (float): The maximum peak width at half height in minutes.

    Returns:
    str: JSON string of chromatograms with peaks filtered by maximum peak width.
    """
    # If the input is a JSON string, load it into a Python object
    if isinstance(chromatograms_json, str):
        chromatograms_df = pd.read_json(chromatograms_json)
    elif isinstance(chromatograms_json, list):
        chromatograms_df = pd.DataFrame(chromatograms_json)
    else:
        raise ValueError("Input must be a JSON string or a list of dictionaries.")

    filtered_chromatograms = []

    for _, chrom in chromatograms_df.iterrows():
        filtered_chrom = {
            'native_id': chrom['native_id'],
            'rt': chrom['rt'],  # Retain the RT of the chromatogram
            'peaks': []  # List to hold filtered peaks
        }
        
        # Extract peaks from the current chromatogram
        peaks = chrom['peaks']
        
        for peak in peaks:
            # Calculate peak width at half height
            intensity = peak['intensity']
            half_height = intensity / 2
            
            # Initialize bounds
            left_bound = None
            right_bound = None
            
            # Iterate over peaks to find bounds
            for p in peaks:
                if p['intensity'] <= half_height:
                    if left_bound is None:
                        left_bound = p['mz']  # Use mz for left bound
                    right_bound = p['mz']  # Update right bound to the last peak below half height
            
            # Calculate peak width
            if left_bound is not None and right_bound is not None:
                peak_width = right_bound - left_bound
                if peak_width <= max_peak_width:
                    filtered_chrom['peaks'].append(peak)

        filtered_chromatograms.append(filtered_chrom)

    return json.dumps(filtered_chromatograms)



def filter_peaks_by_min_relative_valley_depth(chromatograms_json, min_valley_depth):
    """
    Filters peaks in chromatograms based on the minimum relative valley depth.

    Parameters:
    chromatograms_json (str or list): JSON string or list representing the list of chromatograms.
    min_valley_depth (float): The minimum relative valley depth.

    Returns:
    str: JSON string of chromatograms with filtered peaks.
    """
    # Validate the minimum valley depth
    if not (0.05 <= min_valley_depth <= 0.5):
        raise ValueError("Minimum valley depth must be between 0.05 and 0.5.")

    # If the input is a JSON string, load it into a DataFrame
    if isinstance(chromatograms_json, str):
        chromatograms_df = pd.read_json(chromatograms_json)
    elif isinstance(chromatograms_json, list):
        chromatograms_df = pd.DataFrame(chromatograms_json)
    else:
        raise ValueError("Input must be a JSON string or a list of dictionaries.")

    filtered_chromatograms = []

    for _, chromatogram in chromatograms_df.iterrows():
        peaks = chromatogram.get('peaks', [])
        filtered_peaks = []

        # Iterate through the peaks to calculate relative valley depth
        for i in range(len(peaks) - 1):
            current_peak = peaks[i]
            next_peak = peaks[i + 1]

            # Calculate the relative valley depth
            valley_depth = abs(current_peak['intensity'] - next_peak['intensity'])
            lower_peak_intensity = min(current_peak['intensity'], next_peak['intensity'])
            if lower_peak_intensity > 0:  # Avoid division by zero
                relative_valley_depth = valley_depth / lower_peak_intensity
            else:
                relative_valley_depth = 0  # If both peaks are zero, consider valley depth as zero

            # Check if the relative valley depth meets the threshold
            if relative_valley_depth >= min_valley_depth:
                filtered_peaks.append(current_peak)

        # Add the last peak if it wasn't added
        if peaks:
            filtered_peaks.append(peaks[-1])

        # Create a new chromatogram with filtered peaks
        filtered_chrom = {
            'native_id': chromatogram['native_id'],
            'rt': chromatogram['rt'],
            'peaks': filtered_peaks
        }
        filtered_chromatograms.append(filtered_chrom)
    
    #vedi il numero di cromatogrammi
    print(f"Number of chromatograms after filtering: {len(filtered_chromatograms)}")
    # vedi la struttura dei cromatogrammi
    print(filtered_chromatograms[0])

    return json.dumps(filtered_chromatograms)


# ISOTOPE PATTERN DETECTION

def group_isotopes(chromatograms_json: str, additional_elements: List[str], 
                  tolerance_ppm: float = 10, intensity_tolerance: float = 0.2) -> str:
    """
    Raggruppa gli isotopi nei cromatogrammi basandosi sugli elementi specificati.

    Parameters:
    chromatograms_json (str): JSON string dei cromatogrammi
    additional_elements (List[str]): Lista di elementi aggiuntivi da considerare
    tolerance_ppm (float): Tolleranza in ppm per il matching delle masse
    intensity_tolerance (float): Tolleranza per i rapporti di intensità

    Returns:
    str: JSON string dei cromatogrammi con isotopi raggruppati
    """
    # Inizializza l'handler degli isotopi
    isotope_handler = IsotopeHandler()
    
    # Converti il JSON in DataFrame
    if isinstance(chromatograms_json, str):
        chromatograms_df = pd.read_json(chromatograms_json)
    else:
        raise ValueError("Input must be a JSON string")

    # Lista completa degli elementi da considerare
    base_elements = ['C', 'H', 'N', 'O', 'S']
    all_elements = base_elements + additional_elements

    grouped_results = []

    for _, chromatogram in chromatograms_df.iterrows():
        isotope_groups = process_chromatogram_isotopes(
            chromatogram, 
            isotope_handler, 
            all_elements, 
            tolerance_ppm, 
            intensity_tolerance
        )
        
        grouped_results.append({
            'native_id': chromatogram['native_id'],
            'rt': chromatogram['rt'],
            'isotope_groups': isotope_groups
        })
        print(f"Number of isotope groups: {len(isotope_groups)}")   

    return json.dumps(grouped_results)

def process_chromatogram_isotopes(chromatogram: pd.Series, 
                                isotope_handler: IsotopeHandler,
                                elements: List[str],
                                tolerance_ppm: float,
                                intensity_tolerance: float) -> List[Dict]:
    """
    Processa i picchi in un cromatogramma per identificare e raggruppare gli isotopi.
    """
    peaks = chromatogram.get('peaks', [])
    if not peaks:
        return []

    isotope_groups = []
    processed_peaks = set()

    # Ordina i picchi per m/z
    sorted_peaks = sorted(peaks, key=lambda x: x['mz'])

    for i, peak1 in enumerate(sorted_peaks):
        if i in processed_peaks:
            continue

        current_group = {
            'monoisotopic_peak': peak1,
            'isotopes': []
        }

        for j, peak2 in enumerate(sorted_peaks[i+1:], i+1):
            if j in processed_peaks:
                continue

            # Controlla ogni elemento per possibili pattern isotopici
            for element in elements:
                if isotope_handler.is_isotope_pattern(peak1['mz'], peak2['mz'], element, tolerance_ppm):
                    # Verifica il rapporto di intensità
                    theoretical_ratio = isotope_handler.calculate_theoretical_abundance_ratio(
                        element,
                        list(isotope_handler.isotope_masses[element].keys())[0],
                        list(isotope_handler.isotope_masses[element].keys())[1]
                    )
                    
                    observed_ratio = peak2['intensity'] / peak1['intensity']
                    
                    if abs(observed_ratio - theoretical_ratio) <= intensity_tolerance * theoretical_ratio:
                        current_group['isotopes'].append({
                            'peak': peak2,
                            'element': element,
                            'isotope_number': len(current_group['isotopes']) + 2
                        })
                        processed_peaks.add(j)

        if current_group['isotopes']:
            isotope_groups.append(current_group)
            processed_peaks.add(i)

    return isotope_groups

def filter_isotope_groups(grouped_chromatograms_json: str, 
                         min_isotopes: int = 2,
                         max_isotopes: int = 5) -> str:
    """
    Filtra i gruppi di isotopi in base al numero di isotopi nel gruppo.
    """
    grouped_chromatograms = json.loads(grouped_chromatograms_json)
    
    filtered_results = []
    
    for chromatogram in grouped_chromatograms:
        isotope_groups = chromatogram.get('isotope_groups', [])
        filtered_groups = [
            group for group in isotope_groups
            if min_isotopes <= len(group['isotopes']) + 1 <= max_isotopes
        ]
        
        filtered_results.append({
            'native_id': chromatogram['native_id'],
            'rt': chromatogram['rt'],
            'isotope_groups': filtered_groups
        })
    
    return json.dumps(filtered_results)



def group_compounds(filtered_results_json, rt_tolerance=1.0, mass_tolerance_ppm=20, use_isotope_pattern=True):
    """
    Groups compounds based on m/z and retention time tolerances.

    Parameters:
    - filtered_results_json (str): JSON string from the detect compounds step.
    - rt_tolerance (float): Retention time tolerance in minutes.
    - mass_tolerance_ppm (float): Mass tolerance in ppm.
    - use_isotope_pattern (bool): Consider isotope patterns during grouping.

    Returns:
    - str: JSON string of grouped compounds.
    """
    filtered_results = json.loads(filtered_results_json)
    compounds_list = []

    print("Filtered results:", filtered_results)  # Debugging
    print("Number of filtered results:", len(filtered_results))  # Debugging

    for chrom_id, chrom in filtered_results.items():
        print(f"Processing chromatogram ID: {chrom_id}")  # Debugging
        print(f"Chromatogram details: {chrom}")  # Debugging

        if isinstance(chrom, dict):
            rt = chrom.get('rt')
            isotope_groups = chrom.get('isotope_groups', [])
            native_id = chrom.get('native_id')

            for group in isotope_groups:
                monoisotopic_peak = group.get('monoisotopic_peak', {})
                mz = monoisotopic_peak.get('mz')
                intensity = monoisotopic_peak.get('intensity')

                compound = {
                    'mz': mz,
                    'intensity': intensity,
                    'rt': rt,
                    'native_id': native_id,
                }

                if use_isotope_pattern:
                    compound['isotope_pattern'] = [monoisotopic_peak.get('mz')] + [
                        iso.get('mz') for iso in group.get('isotopes', [])
                    ]

                compounds_list.append(compound)
        else:
            print(f"Unexpected structure for chromatogram ID {chrom_id}: {chrom}")  # Debugging

    print("Compounds list:", compounds_list)  # Debugging

    compound_groups = []

    for compound in compounds_list:
        placed = False
        for group in compound_groups:
            rep = group[0]
            delta_mz = abs(compound['mz'] - rep['mz'])
            ppm = (delta_mz / rep['mz']) * 1e6
            delta_rt = abs(compound['rt'] - rep['rt'])

            print(f"Comparing compound {compound} with group representative {rep}")  # Debugging
            print(f"delta_mz: {delta_mz}, ppm: {ppm}, delta_rt: {delta_rt}")  # Debugging

            if ppm <= mass_tolerance_ppm and delta_rt <= rt_tolerance:
                if use_isotope_pattern:
                    overlap = set(compound.get('isotope_pattern', [])).intersection(
                        rep.get('isotope_pattern', [])
                    )
                    if not overlap:
                        continue
                group.append(compound)
                placed = True
                break

        if not placed:
            compound_groups.append([compound])

    print("Compound groups:", compound_groups)  # Debugging

    grouped_compounds = []
    for idx, group in enumerate(compound_groups):
        group_mz = sum(c['mz'] for c in group) / len(group)
        group_rt = sum(c['rt'] for c in group) / len(group)
        total_intensity = sum(c['intensity'] for c in group)
        grouped_compounds.append({
            'group_id': idx,
            'mz': group_mz,
            'rt': group_rt,
            'intensity': total_intensity,
            'members': group
        })

    print("Grouped compounds:", grouped_compounds)  # Debugging

    return json.dumps(grouped_compounds)



