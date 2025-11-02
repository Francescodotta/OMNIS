import subprocess

cmd = [
    "FeatureFinderMetabo",
    "-in", "/media/datastorage/it_cast/metabolomica/test/CC1.mzML",
    "-out", "/media/datastorage/it_cast/metabolomica/test/features.featureXML",
]

# Run the command
try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("FeatureFinderMetabo completed successfully.")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"Error running FeatureFinderMetabo: {e}")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")