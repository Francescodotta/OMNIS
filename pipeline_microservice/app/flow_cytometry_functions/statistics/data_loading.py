import pandas as pd
import flowkit as fk
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from typing import List, Tuple, Dict
import numpy as np
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import os
from app.models.flow_cytometry import FlowCytometryModel
from cryptography.fernet import Fernet

FLOW_CYTOMETRY_SECRET_KEY = os.getenv('FLOW_CYTOMETRY_SECRET_KEY')

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

def load_control_treatment_maps(progressive_ids: List[str]) -> List[Tuple[str, str]]:
    """
    Load control and treatment sample maps from given progressive IDs.

    Args:
        progressive_ids (List[str]): List of progressive IDs to load maps from.

    Returns:
        List[Tuple[str, str]]: List of tuples containing (control_file_path, treatment_file_path)
    """
    control_treatment_pairs = []
    
    # Dictionary to group files by their control_id
    control_map = {}
    treatment_map = {}
    
    for pid in progressive_ids:
        model = FlowCytometryModel.find_by_progressive_id(int(pid))
        print("Loaded model:", model)
        if model is None:
            print(f"Model with progressive_id {pid} not found.")
            continue
        
        # create the tuple (file_path, control_id)
        encrypted_file_path = model.get('file_path')
        if encrypted_file_path is None:
            print(f"File path for progressive_id {pid} is None.")
            continue
        treatment_file_path = decrypt_data(encrypted_file_path) # treatment sample
        control_model = FlowCytometryModel.find_by_progressive_id(int(model.get('control_id')))
        control_file_path = control_model.get('file_path')
        decrypted_control_file_path = decrypt_data(control_file_path) if control_file_path else None
        print(f"Progressive ID: {pid}, Control ID: {model.get('control_id')}, Treatment File: {treatment_file_path}, Control File: {decrypted_control_file_path}")
        # create the tuple (control_file_path, treatment_file_path)
        if decrypted_control_file_path:
            control_treatment_pairs.append((decrypted_control_file_path, treatment_file_path))
        
        
    
    return control_treatment_pairs