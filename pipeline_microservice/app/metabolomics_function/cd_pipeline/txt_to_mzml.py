import os
import glob
import subprocess

def txt_to_mgf(txt_file, mgf_file):
    with open(txt_file, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        return  # Skip empty files
    
    # Extract HMDB ID from filename (e.g., HMDB0014383 from HMDB0014383_msms_...)
    hmdb_id = os.path.basename(txt_file).split('_')[0]
    
    # Assume first m/z as precursor (placeholder for predicted spectra)
    precursor_mz = float(lines[0].split()[0])
    
    with open(mgf_file, 'w') as f:
        f.write("BEGIN IONS\n")
        f.write(f"TITLE={hmdb_id}\n")
        f.write(f"PEPMASS={precursor_mz} 0\n")  # Precursor m/z and intensity (set intensity to 0)
        f.write("CHARGE=1+\n")
        f.write("RTINSECONDS=0\n")  # Placeholder RT
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                mz, intensity = parts
                f.write(f"{mz} {intensity}\n")
        f.write("END IONS\n")

# Step 1: Convert all TXT files to MGF
txt_files = glob.glob("/media/datastorage/it_cast/omnis_microservice_db/tools/predicted_msms_hmdb/*.txt")
for txt_file in txt_files:
    mgf_file = txt_file.replace('.txt', '.mgf')
    txt_to_mgf(txt_file, mgf_file)
    print(f"Converted {txt_file} to {mgf_file}")

print("TXT to MGF conversion complete!")

# Step 2: Use msconvert to convert all MGF files to a single merged mzML file
msconvert_path = "/media/datastorage/it_cast/omnis_microservice_db/tools/msconvert"
output_file = "library.mzML"

# Use find and xargs to handle large number of files without argument limit
command = f"find . -name '*.mgf' | xargs {msconvert_path} --mzML --merge --outfile {output_file}"
try:
    subprocess.run(command, shell=True, check=True)
    print(f"Conversion to {output_file} complete!")
except subprocess.CalledProcessError as e:
    print(f"Error during msconvert: {e}")