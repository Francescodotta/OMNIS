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



# # Funzione per effettuare lo scraping dei metaboliti
# def scrape_metabolite(url):
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')
    
#     # Trova il main con role="main"
#     main_content = soup.find('main')
    
#     # Trova la tabella con la classe "content-table"
#     table = main_content.find('table', {'class': 'content-table'})
#     if not table:
#         return None
#     tr = table.find_all('tr')
#     # se non trova la tabella restituisce None
#     if not tr:
#         return None
    
#     # Dizionario per memorizzare i dati del metabolita
#     metabolite_data = {}
    
#     for i in tr:
#         if i.find('th'):
#             header = i.find('th').string
#             if i.find('td'):
#                 value = i.find('td').string
#                 if header == "Common Name":
#                     metabolite_data['name'] = value
#                 elif header == "Average Molecular Weight":
#                     metabolite_data['average_molecular_weight'] = float(value)
#                 elif header == "Monoisotopic Molecular Weight":
#                     metabolite_data['monoisotopic_molecular_weight'] = float(value)
#                 elif header == "SMILES":
#                     metabolite_data['smiles'] = value
    
#     # Aggiungi l'ID del metabolita
#     metabolite_data['id'] = url.split('/')[-1]
    
#     return metabolite_data


# prendi il file in input e salvalo nel giusto path


def convert_raw_to_mzml(raw_file_path):
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
    mzml_file_path = os.path.join(METABOLOMICS_SAVE_PATH, os.path.basename(raw_file_path).replace('.raw', '.mzML'))
    return mzml_file_path


# inserire tutte le funzioni che servono per effettuare lo step di select spectra 


  