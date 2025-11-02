import json
import pandas as pd
import numpy as np


def filter_peaks(mzarray, intarray, min_mz=0, max_mz=1000):
        filtered_peaks = [(mz, intensity) for mz, intensity in zip(mzarray, intarray) if min_mz <= mz <= max_mz]
        if filtered_peaks:
            mzs, intensities = zip(*filtered_peaks)
            return list(mzs), list(intensities)
        else:
            return [], []
        
# funzione per calcolare il rapporto segnale rumore
def calculate_sn_ratio(intensities):
    # Calculate noise level as the median of the intensities
    noise_level = np.median(intensities)
    # Avoid division by zero
    if (noise_level == 0):
        noise_level = 1
    # Calculate S/N ratios
    sn_ratios = intensities / noise_level
    # Return the mean of the S/N ratios
    return np.mean(sn_ratios)


# funzione per filtrare gli spettri in base al tempo di RT
def filter_spectra_RT_time_from_json(exp_json, lower_RT=None, higher_RT=None):
    """
    Filtra gli spettri da un JSON in base a un intervallo di RT.
    
    Args:
        exp_json (str): Dati in formato JSON che rappresentano gli spettri.
        lower_RT (float, optional): Valore minimo di RT.
        higher_RT (float, optional): Valore massimo di RT.
    
    Returns:
        str: Dati in formato JSON con gli spettri filtrati.
    """
    # Convert JSON to DataFrame
    df = pd.read_json(exp_json)
    
    # Log the length of the spectra
    print(f"Number of spectra before filtering: {len(df)}")
    
    # Filter the DataFrame based on RT values
    if lower_RT is not None:
        df = df[df['RT'] > lower_RT]
    if higher_RT is not None:
        df = df[df['RT'] < higher_RT]
    
    # Log the length of the filtered spectra
    print(f"Number of spectra after filtering: {len(df)}")
    
    return df.to_json()

# filtro spettri in base agli scan
def filter_spectra_scan_from_json(spectra_json, first_scan=None, last_scan=None):
    """
    Filtra gli spettri in base al numero di scansione, partendo da un JSON.
    
    Args:
        spectra_json (dict): Dati JSON contenenti gli spettri e i loro metadati.
        first_scan (int, optional): Numero minimo di scansione. Se None, non si applica il limite inferiore.
        last_scan (int, optional): Numero massimo di scansione. Se None, non si applica il limite superiore.

    Returns:
        dict: JSON filtrato contenente solo gli spettri che rispettano i criteri.
    """
    # Converti il JSON in un DataFrame per facilitare il filtro
    df = pd.read_json(spectra_json)
    
    # Estrai i numeri di scansione dai valori 'scan_number'
    df['scan_number'] = df['scan_number'].str.extract(r'scan=(\d+)').astype(int)
    
    # Applica i filtri in base a first_scan e last_scan
    if first_scan is not None:
        df = df[df['scan_number'] >= first_scan]
    if last_scan is not None:
        df = df[df['scan_number'] <= last_scan]
    print(f"Number of spectra after filtering: {len(df)}")
    
    # Converti il DataFrame filtrato di nuovo in JSON
    return df.to_json()


def ignore_scans(json_exp, scans_to_ignore):
    """
    Ignora gli spettri specificati da scans_to_ignore.
    
    Args:
        json_exp (str): JSON contenente gli spettri.
        scans_to_ignore (list): Lista di numeri di scansione da ignorare.
        
    Returns:
        str: JSON con gli spettri filtrati.
    """
    
    df = pd.read_json(json_exp)
    df['scan_number'] = df['scan_number'].str.extract(r'scan=(\d+)').astype(int)
    df = df[~df['scan_number'].isin(scans_to_ignore)]
    # print la lunghezza del df
    print(f"Number of spectra after filtering: {len(df)}")
    return df.to_json()
    

def filter_min_peak_count_from_json(spectra_json, min_peak_count):
    """
    Filtra gli spettri in base al numero minimo di picchi, partendo da un JSON.
    
    Args:
        spectra_json (str): JSON contenente gli spettri e i loro metadati.
        min_peak_count (int): Numero minimo di picchi richiesti per mantenere uno spettro.

    Returns:
        str: JSON contenente solo gli spettri che rispettano il criterio.
    """
    # Converti il JSON in un DataFrame per facilitare il filtro
    df = pd.read_json(spectra_json)

    # Calcola il numero di picchi per ogni spettro
    df['peak_count'] = df['mzarray'].apply(len)
    print(df['peak_count'].head())
    # Filtra gli spettri in base al numero minimo di picchi
    filtered_df = df[df['peak_count'] >= min_peak_count]

    # Rimuovi la colonna temporanea 'peak_count'
    filtered_df = filtered_df.drop(columns=['peak_count'])
    # print number of spectra
    print(f"Number of spectra after filtering: {len(filtered_df)}")
    # Converti il DataFrame filtrato di nuovo in JSON
    return filtered_df.to_json()


def filter_polarity_from_json(spectra_json, polarity):
    # json in dataframe
    df = pd.read_json(spectra_json)
    # filtra in base alla polarità
    filtered_df = df[df['polarity'] == polarity]
    # print number of spectra
    print(f"Number of spectra after filtering: {len(filtered_df)}")
    # ritorna in formato json
    return filtered_df.to_json()


def filter_MS1_range_from_json(df_json, min_MZ, max_MZ):
    """
    Filtra i picchi degli spettri di livello MS1 in base a un intervallo di m/z, utilizzando un JSON serializzato da un DataFrame.

    Args:
        df_json (str): JSON rappresentativo del DataFrame contenente i dati degli spettri.
        interval (list): Intervallo di m/z (min_mz, max_mz).

    Returns:
        str: JSON del DataFrame filtrato.
    """
    # Converti il JSON in DataFrame
    df = pd.read_json(df_json)
    print(f"Number of spectra before MS1 m/z filter: {len(df)}")
    # Filtra solo gli spettri con ms_level == 1
    df_ms1 = df[df['ms_level'] == 1].copy()

    # Applica il filtro ai picchi
    df_ms1[['mzarray', 'intarray']] = df_ms1.apply(
        lambda row: pd.Series(filter_peaks(row['mzarray'], row['intarray'], min_MZ, max_MZ)), axis=1
    )

    # Rimuovi gli spettri senza picchi
    df_ms1 = df_ms1[df_ms1['mzarray'].apply(len) > 0]

    # Combina di nuovo gli spettri filtrati con gli altri livelli di ms_level
    df_filtered = pd.concat([df[df['ms_level'] != 1], df_ms1])

    # Log per debug
    print(f"Number of spectra after MS1 m/z filter: {len(df_filtered)}")

    # Serializza di nuovo il DataFrame in JSON
    return df_filtered.to_json()


# funzione che filtra gli spettri in base al rapporto segnale/rumore
def filter_sn_threshold(df_json, sn_threshold):
    df = pd.read_json(df_json)
    print(f"Number of spectra before S/N filtering: {len(df)}")
    # Calcola il rapporto segnale rumore per ogni spettro
    df['sn_ratios'] = df['intarray'].apply(calculate_sn_ratio)
    # Filtra gli spettri in base al rapporto segnale rumore
    df_filtered = df[df['sn_ratios'] >= sn_threshold]
    # Rimuovi la colonna temporanea 'sn_ratios'
    df_filtered = df_filtered.drop(columns=['sn_ratios'])
    # Log per debug
    print(f"Number of spectra after S/N filtering: {len(df_filtered)}")
    # Serializza di nuovo il DataFrame in JSON
    return df_filtered.to_json()

