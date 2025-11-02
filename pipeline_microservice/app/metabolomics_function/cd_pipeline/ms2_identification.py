import pyopenms as oms
import pandas as pd
import os
import subprocess

def run_ms2_identification(mzml_file, library_file, output_csv, mztab_output="ms2_identifications.mztab"):
    """
    Perform MS2 identification using OpenMS command-line tool MetaboliteSpectralMatcher.
    Parses MzTab output manually with debugging.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_csv)
    os.makedirs(output_dir, exist_ok=True)
    
    # Build the command
    cmd = [
        "MetaboliteSpectralMatcher",
        "-in", mzml_file,
        "-database", library_file,
        "-out", mztab_output,
    ]
    
    # Run the command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("MetaboliteSpectralMatcher completed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running MetaboliteSpectralMatcher: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return pd.DataFrame()  # Return empty DataFrame on error
    
    # Debug: Print the first 20 lines of the MzTab file
    print("First 20 lines of MzTab file:")
    with open(mztab_output, 'r') as f:
        for i, line in enumerate(f):
            if i < 20:
                print(f"Line {i}: {line.strip()}")
            else:
                break
    
    # Parse the MzTab file manually
    identifications = []
    with open(mztab_output, 'r') as f:
        lines = f.readlines()
    
    in_sml_section = False
    for line in lines:
        line = line.strip()
        if line.startswith("SMH"):  # Small molecule header
            print(f"Header: {line}")
            in_sml_section = True
            continue
        elif line.startswith("SML") and in_sml_section:
            parts = line.split('\t')
            print(f"SML line: {parts}")  # Debug: Print the parts
            if len(parts) > 5:  # Adjust based on actual number of columns
                identifications.append({
                    'precursor_mz': float(parts[1]) if parts[1] and parts[1] != 'null' else 0.0,
                    'precursor_rt': float(parts[2]) if parts[2] and parts[2] != 'null' else 0.0,
                    'score': float(parts[3]) if parts[3] and parts[3] != 'null' else 0.0,
                    'adduct': parts[4] if parts[4] and parts[4] != 'null' else '',
                    'formula': parts[5] if parts[5] and parts[5] != 'null' else ''
                })
    
    print(f"Number of identifications parsed: {len(identifications)}")
    
    # Save to CSV
    df = pd.DataFrame(identifications)
    df.to_csv(output_csv, index=False)
    print(f"MS2 identifications saved to {output_csv}")
    return df

if __name__ == "__main__":
    mzml_file = "/media/datastorage/it_cast/metabolomica/test/CC1.mzML"
    library_file = "/media/datastorage/it_cast/omnis_microservice_db/tools/GNPS-LIBRARY.mzML"
    output_csv = "/media/datastorage/it_cast/metabolomica/test/ms2_output/ms2_identifications.csv"
    mztab_output = "/media/datastorage/it_cast/metabolomica/test/ms2_output/ms2_identifications.mztab"
    run_ms2_identification(mzml_file, library_file, output_csv, mztab_output)