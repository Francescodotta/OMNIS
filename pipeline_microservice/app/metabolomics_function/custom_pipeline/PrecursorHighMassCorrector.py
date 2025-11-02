import subprocess
import os

mzml_file_path = ""
mzml_file_output_path = ""

cmd = [
    "HighResPrecursorMassCorrector",
    "-in", mzml_file_path,
    "-out", mzml_file_output_path
]



#### function to run the process 