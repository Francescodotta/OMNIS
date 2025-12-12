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


def extract_file_paths(file_tuples: List[Tuple[str, str]]) -> List[str]:
    """
    
    

    Args:
        file_tuples (List[Tuple[str, str]]): Tuple containing file path of the treatment and control samples.

    Returns:
        List[str]: list of file paths for both treatment and control samples.
    """
    file_paths = []
    for treatment_path, control_path in file_tuples:
        file_paths.append(treatment_path)
        file_paths.append(control_path)
    return file_paths


# extract parameters from fcs files
def load_fcs_files_as_df(file_tuples: List[Tuple[str, str]]) -> pd.DataFrame:
    """
    Function to load FCS files and convert them to a combined pandas DataFrame.
    
    Args:
        file_paths (List[Tuple[str, str]]): List of tuples containing file paths for treatment and control samples.
    
    Returns:
        pd.DataFrame: Combined DataFrame containing data from all FCS files with an additional 'sample_id' column.
    """
    all_data = []
    # convert list of tuples to flat list
    file_paths = extract_file_paths(file_tuples)
    for file_path in file_paths:
        sample_name = os.path.basename(file_path).split('.')[0]
        df = fk.Sample(file_path).as_dataframe(source="raw")
        df['sample_id'] = sample_name
        all_data.append(df)
    combined_df = pd.concat(all_data, ignore_index=True)
    # LOGGING STATEMENT
    print(f"Loaded {len(file_paths)} FCS files into a combined DataFrame with shape {combined_df.shape}.")
    # number of samples in the df
    print(f"Number of unique samples: {combined_df['sample_id'].nunique()}")
    return combined_df


# raw means
def extract_raw_means(df: pd.DataFrame, sample_column: str = 'sample_id') -> pd.DataFrame:
    """
    Function to extract raw means for each sample in the DataFrame.
    
    Args:
        df (pd.DataFrame): Input DataFrame containing flow cytometry data.
        sample_column (str): Column name that identifies different samples.
    
    Returns:
        pd.DataFrame: DataFrame containing raw means for each sample.
    """
    mean_df = df.groupby(sample_column).mean().reset_index()
    print(mean_df.shape)
    # LOGGING STATEMENT
    print(f"Extracted raw means for {mean_df.shape[0]} samples.")
    return mean_df


def apply_standard_scaling(df: pd.DataFrame, id_column: str = 'sample_id') -> pd.DataFrame:
    """
    Function to apply standard scaling to specified feature columns in the DataFrame.
    
    Args:
        df (pd.DataFrame): Input DataFrame containing flow cytometry data.
        id_column (str): Column name to preserve (e.g., 'sample_id'). Default is 'sample_id'.
    
    Returns:
        pd.DataFrame: DataFrame with scaled feature columns and preserved ID column.
    """
    scaler = StandardScaler()
    
    # Select only numeric columns for scaling
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Create a copy of the dataframe
    df_scaled = df.copy()
    
    # Scale only numeric columns
    df_scaled[numeric_columns] = scaler.fit_transform(df[numeric_columns])
    
    # LOGGING STATEMENT
    print(f"Applied standard scaling to {len(numeric_columns)} numeric columns.")
    print(f"Preserved column: {id_column}")
    
    return df_scaled

def remove_outliers_iqr(df, multiplier=1.5, id_column='sample_id'):
    """
    Rimuove outlier usando il metodo IQR (Interquartile Range).
    Per ogni parametro (colonna numerica), valori fuori da [Q1 - k*IQR, Q3 + k*IQR] 
    vengono rimossi (impostati a NaN).
    
    Args:
        df: DataFrame con dati di flow cytometry
        multiplier: 1.5 (default) è standard, 3.0 è più conservativo
        id_column: colonna da preservare (default: 'sample_id')
    
    Returns:
        DataFrame con outlier rimossi (come NaN)
    """
    # Select numeric columns only
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove id_column from numeric columns if it's numeric
    if id_column in numeric_columns:
        numeric_columns.remove(id_column)
    
    df_cleaned = df.copy()
    n_outliers_total = 0
    outlier_info = []
    
    # Apply IQR only to numeric columns (excluding id_column)
    for col in numeric_columns:
        Q1 = df_cleaned[col].quantile(0.25)
        Q3 = df_cleaned[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        # Identifica outlier
        outliers_mask = (df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)
        n_outliers = outliers_mask.sum()
        
        if n_outliers > 0:
            outlier_info.append({
                'parameter': col,
                'n_outliers': n_outliers,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'Q1': Q1,
                'Q3': Q3,
                'IQR': IQR
            })
            n_outliers_total += n_outliers
            # Rimuovi outlier (imposta a NaN)
            df_cleaned.loc[outliers_mask, col] = np.nan
    
    # LOGGING
    print(f"Applied IQR outlier removal to {len(numeric_columns)} numeric columns.")
    print(f"Total outliers found: {n_outliers_total}")
    print(f"Preserved column: {id_column}")
    
    return df_cleaned


