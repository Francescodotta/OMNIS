import requests
import os, subprocess
from dotenv import load_dotenv
import pyopenms as oms
import pandas as pd
import numpy as np

load_dotenv()
METABOLOMICS_SAVE_PATH = os.getenv("METABOLOMICS_SAVE_PATH")
TOOLS_PATH = os.getenv("TOOLS_PATH")
THERMO_FILE_PARSER_PATH = os.path.join(TOOLS_PATH, "thermofisher", "ThermoRawFileParser.exe")


def convert_raw_to_mzml(raw_file_path, project_id):
    # Construct the command to convert the raw file to mzML
    command = [
        "mono", THERMO_FILE_PARSER_PATH,
        "-i", raw_file_path,
        "-o", METABOLOMICS_SAVE_PATH,
        "-f", "1"  # Format 1 corresponds to mzML
    ]

    # Run the command
    subprocess.run(command, check=True)

    # Return the path of the converted mzML file
    mzml_file_path = os.path.join(METABOLOMICS_SAVE_PATH, f'project_{project_id}', os.path.basename(raw_file_path).replace('.raw', '.mzML'))
    return mzml_file_path




  