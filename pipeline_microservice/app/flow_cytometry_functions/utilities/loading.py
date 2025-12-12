import flowkit as fk
import pandas as pd
from dotenv import load_dotenv
import os
from typing import List
from app.models import flow_cytometry
import logging
from app.models.flow_cytometry import FlowCytometryModel
from cryptography.fernet import Fernet



# set up logging
logger = logging.getLogger(__name__)


FLOW_CYTOMETRY_SECRET_KEY = os.getenv('FLOW_CYTOMETRY_SECRET_KEY')



# Load environment variables
load_dotenv()

# Define the path to the FCS files  
FLOW_CYTOMETRY_SAVE_PATH = os.getenv("FLOW_CYTOMETRY_SAVE_PATH")


# get project_id and metadata
def decrypt_data(data):
    """
    Decrypts data using Fernet symmetric encryption
    
    Args:
        data (bytes): Data to decrypt
    
    Returns:
        str: Decrypted data
    """
    try:
        fernet = Fernet(FLOW_CYTOMETRY_SECRET_KEY)
        return fernet.decrypt(data).decode('utf-8')
    except Exception as e:
        print(f"Error decrypting data: {str(e)}")
        raise Exception("Failed to decrypt data")
    

# get the flow cytometry db from file path
def get_flow_cytometry_db(file_path: str):
    # decrypt the file path
    decrypted_path = decrypt_data(file_path)
        




def load_fcs_files(file_paths: List[str], file_ids: List[str], filenames: List[str], metadata: dict) -> pd.DataFrame:
    """
    Load multiple FCS files into a FlowData object and associate progressive_id and filename to each sample.
    
    Args:
        file_paths (List[str]): List of file paths to FCS files.
        file_ids (List[str]): List of progressive_ids corresponding to each file.
        filenames (List[str]): List of filenames corresponding to each file.
    
    Returns:
        pd.DataFrame: DataFrame containing all loaded samples with metadata.
    """
    try:
        samples = fk.load_samples(file_paths)
        dataframes = []
        # Associa ogni sample con il suo id e filename (stesso ordine delle liste)
        for idx, sample in enumerate(samples):
            df = sample.as_dataframe(source='raw', col_multi_index=False)
            print("DataFrame shape:", df.shape, "\n", "DataFrame columns:", df.columns)
            # Aggiungi le colonne progressive_id e filename
            df['sample_id'] = sample
            df['file_id'] = file_ids[idx]
            df['filename'] = filenames[idx]
            # add metadata columns
            for key, value in metadata.items():
                print(f"Adding metadata column: {key} with value: {value}")
                df[key] = pd.Series([str(value[idx])] * len(df), index=df.index)
            dataframes.append(df)
        combined_df = pd.concat(dataframes, ignore_index=True)
        del samples
        del dataframes
        return combined_df
    except Exception as e:
        logger.error(f"Error loading FCS files: {str(e)}")
        raise e
