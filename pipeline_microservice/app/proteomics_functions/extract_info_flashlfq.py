import pandas as pd
from pyteomics import mzml
import os
import re
import io  # aggiungi questo import

def get_retention_times(mzml_path):
    rt_dict = {}
    print(f"Parsing mzML: {mzml_path}")
    with mzml.MzML(mzml_path) as reader:
        for spectrum in reader:
            scan_id = spectrum.get('id', '')
            if 'scan=' in scan_id:
                try:
                    scan_number = int(scan_id.split('scan=')[-1].split()[0])
                    rt = spectrum['scanList']['scan'][0]['scan start time']
                    rt_dict[scan_number] = rt
                except Exception as e:
                    print(f"Error parsing spectrum {scan_id}: {e}")
    print(f"Extracted {len(rt_dict)} retention times from mzML.")
    return rt_dict

def extract_protein_accession(protein_string):
    # Estrae solo l'accession da una stringa tipo "sp|P12345|PROTEIN_HUMAN"
    pattern = r'\|([A-Z0-9]+)\|'
    match = re.search(pattern, protein_string)
    if match:
        return match.group(1)
    else:
        return protein_string

def parse_pin(pin_path, mzml_path):
    mzml_filename = os.path.basename(mzml_path)
    rt_dict = get_retention_times(mzml_path)
    rows = []

    print(f"Parsing Percolator .pin: {pin_path}")
    # Leggi il file .pin saltando eventuali righe di commento
    with open(pin_path) as f:
        lines = [line for line in f if not line.startswith('#')]
    df = pd.read_csv(io.StringIO(''.join(lines)), sep='\t')

    charge_columns = [
        'charge_1', 'charge_2', 'charge_3', 'charge_4',
        'charge_5', 'charge_6', 'charge_7_or_more'
    ]

    for idx, row in df.iterrows():
        base_seq = row['Peptide']
        theo_mass = row['ExpMass']
        charge = None
        for col in charge_columns:
            if col in row and row[col] > 0:
                charge = row[col]
                break
        if charge is None:
            print(f"Skipping row {idx}: No valid precursor charge found (Peptide: {row['Peptide']}, ScanNr: {row['ScanNr']})")
            continue
        scan = int(row['ScanNr'])
        protein_accession = row['Proteins']
        rt = rt_dict.get(scan, row['retentiontime'] if 'retentiontime' in row else None)
        # Estrai solo l'accession se ci sono più proteine separate da ';'
        protein_accession = ';'.join([extract_protein_accession(p) for p in str(protein_accession).split(';')])
        rows.append({
            "File Name": mzml_filename,
            "Base Sequence": base_seq,
            "Full Sequence": base_seq,  # Modifica qui se vuoi aggiungere modifiche
            "Peptide Monoisotopic Mass": theo_mass,
            "Scan Retention Time": rt,
            "Precursor Charge": int(charge),
            "Protein Accession": protein_accession
        })
    print(f"Parsed {len(rows)} PSMs from .pin.")
    return pd.DataFrame(rows)

if __name__ == "__main__":
    pin_path = "/media/datastorage/it_cast/omnis_microservice_db/test_db/20250228_04_01.pin"
    mzml_path = "/media/datastorage/it_cast/omnis_microservice_db/test_db/20250228_04_01.mzML"
    output_path = "/media/datastorage/it_cast/omnis_microservice_db/test_db/flashlfq_input.tsv"

    df = parse_pin(pin_path, mzml_path)
    df.to_csv(output_path, sep="\t", index=False)
    print(f"File pronto per FlashLFQ salvato in: {output_path}")