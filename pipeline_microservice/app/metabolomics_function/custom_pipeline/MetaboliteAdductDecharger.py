import os
import subprocess

cmd = [
    "MetaboliteAdductDecharger",
    "-in", "/media/datastorage/it_cast/metabolomica/test/features.featureXML",
    "-out_fm", "/media/datastorage/it_cast/metabolomica/test/decharged.featureXML",
    "-out_cm", "/media/datastorage/it_cast/metabolomica/test/decharged.consensusXML",
]

try:
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("MetaboliteAdductDecharger completed successfully.")

except subprocess.CalledProcessError as e:
    print(f"Error running MetaboliteAdductDecharger: {e}")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")