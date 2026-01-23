import requests
import os, subprocess
from dotenv import load_dotenv
import pyopenms as oms
import pandas as pd
import numpy as np
import shutil

load_dotenv()
METABOLOMICS_SAVE_PATH = os.getenv("METABOLOMICS_SAVE_PATH")
TOOLS_PATH = os.getenv("TOOLS_PATH", "")
THERMO_FILE_PARSER_PATH = os.environ.get(
    "THERMO_RAW_FILE_PARSER_PATH",
    os.path.join("/tools", "ThermoRawFileParser.exe")
)

def convert_raw_to_mzml(raw_file_path, project_id):
    if not METABOLOMICS_SAVE_PATH:
        raise RuntimeError("METABOLOMICS_SAVE_PATH non impostato")

    project_dir = os.path.join(METABOLOMICS_SAVE_PATH, f'project_{project_id}')
    os.makedirs(project_dir, exist_ok=True)

    parser = THERMO_FILE_PARSER_PATH
    # resolve if a name given
    if not os.path.isabs(parser):
        found = shutil.which(parser)
        if found:
            parser = found

    if not os.path.exists(parser):
        raise FileNotFoundError(f"ThermoRawFileParser non trovato: {parser}")

    # require mono to run .exe on Linux
    if not shutil.which("mono"):
        raise RuntimeError("mono non installato nel container; necessario per eseguire il .exe")

    command = ["mono", parser, "-i", raw_file_path, "-o", project_dir, "-f", "1"]

    try:
        proc = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"ThermoRawFileParser failed (rc={e.returncode})\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        raise

    mzml_file_path = os.path.join(project_dir, os.path.basename(raw_file_path).replace('.raw', '.mzML'))
    return mzml_file_path




