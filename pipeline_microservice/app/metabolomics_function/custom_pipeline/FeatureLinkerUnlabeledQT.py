import subprocess
import os

cmd = [
    "FeatureLinkerUnlabeledQT",
    "-in",
    "/media/datastorage/it_cast/metabolomica/test/decharged.consensusXML",
    "-out",
    "/media/datastorage/it_cast/metabolomica/test/linked.consensusXML",
]   

try:
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("FeatureLinkerUnlabeledQT completed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error running FeatureLinkerUnlabeledQT: {e}")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")