import subprocess
import os

cmd = [
    "FileConverter",
    "-in", "/media/datastorage/it_cast/metabolomica/test/linked.consensusXML",
    "-out", "/media/datastorage/it_cast/metabolomica/test/linked.featureXML",
]

try:
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("FileConverter completed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error running FileConverter: {e}")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")