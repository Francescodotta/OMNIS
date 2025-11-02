import os 
import subprocess


mzml_file_path = ""
mzml_output_path=""

cmd = [
    "SiriusAdapter",
    "-in", mzml_file_path,
    "-out", mzml_output_path
]


### function to run the command 