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


# generate various dfs for each sample
def generate_sample_dfs(df: pd.DataFrame, sample_column: str = 'sample_id') -> Dict[str, pd.DataFrame]:
    """
    Function to generate a dictionary of DataFrames for each unique sample in the input DataFrame.
    
    Args:
        df (pd.DataFrame): Input DataFrame containing flow cytometry data with a sample identifier column.
        sample_column (str): Name of the column that contains sample identifiers.
    
    Returns:
        Dict[str, pd.DataFrame]: Dictionary where keys are sample identifiers and values are corresponding DataFrames.
    """
    sample_dfs = {}
    unique_samples = df[sample_column].unique()
    for sample in unique_samples:
        sample_df = df[df[sample_column] == sample].copy()
        sample_dfs[sample] = sample_df
        # LOGGING STATEMENT
        print(f"Generated DataFrame for sample '{sample}' with shape {sample_df.shape}.")
    return sample_dfs


# read tuple for treatment-control pairs and compute pairwise differences
def compute_pairwise_differences(df: pd.DataFrame, pairs: List[Tuple[str, str]], sample_column: str = 'sample_id') -> pd.DataFrame:
    """
    Function to compute pairwise differences between treatment and control samples.
    
    Args:
        df (pd.DataFrame): DataFrame containing flow cytometry data.
        pairs (List[Tuple[str, str]]): List of tuples containing file paths for treatment and control samples.
        sample_column (str): Name of the column that contains sample identifiers.
    
    Returns:
        pd.DataFrame: DataFrame containing pairwise differences with columns for treatment, control, and marker differences.
    """
    # Extract sample names from file paths in pairs
    sample_pairs = []
    for control_path, treatment_path in pairs:
        # Extract filename without extension from path
        treatment_name = os.path.splitext(os.path.basename(treatment_path))[0]
        control_name = os.path.splitext(os.path.basename(control_path))[0]
        sample_pairs.append((treatment_name, control_name))
        print(f"Mapped paths to samples: {treatment_name} (treatment) vs {control_name} (control)")
    
    # Generate sample DataFrames
    sample_dfs = generate_sample_dfs(df, sample_column)
    
    # Get marker names - handle both tuple and string column names
    marker_columns = []
    for col in df.columns:
        if isinstance(col, tuple):
            # Extract first element of tuple
            col_name = col[0]
        else:
            col_name = col
        
        # Skip sample_id column
        if col_name != sample_column and col_name != '':
            marker_columns.append(col)
    
    print(f"Marker columns ({len(marker_columns)}): {[c[0] if isinstance(c, tuple) else c for c in marker_columns[:5]]}...")
    
    pairwise_data = []
    for (treatment_id, control_id) in sample_pairs:
        if treatment_id not in sample_dfs:
            print(f"Warning: Treatment sample '{treatment_id}' not found in DataFrame")
            continue
        if control_id not in sample_dfs:
            print(f"Warning: Control sample '{control_id}' not found in DataFrame")
            continue
            
        treatment_df = sample_dfs[treatment_id]
        control_df = sample_dfs[control_id]
        
        # Ensure both DataFrames have the same shape
        min_length = min(len(treatment_df), len(control_df))
        treatment_values = treatment_df[marker_columns].iloc[:min_length].values
        control_values = control_df[marker_columns].iloc[:min_length].values
        
        differences = treatment_values - control_values
        
        # Create records with actual marker names
        for diff_values in differences:
            record = {
                'treatment_id': treatment_id,
                'control_id': control_id,
            }
            # Use actual marker names as column names (extract first element if tuple)
            for marker_col, value in zip(marker_columns, diff_values):
                if isinstance(marker_col, tuple):
                    marker_name = marker_col[0]  # Use only first element
                else:
                    marker_name = marker_col
                record[marker_name] = value
            pairwise_data.append(record)
        
        # LOGGING STATEMENT
        print(f"Computed pairwise differences for treatment '{treatment_id}' and control '{control_id}'.")
    
    pairwise_df = pd.DataFrame(pairwise_data)
    print(f"Pairwise differences DataFrame shape: {pairwise_df.shape}")
    print(f"Columns: {list(pairwise_df.columns)[:10]}...")
    
    return pairwise_df


# ========== CALCOLO METRICHE STATISTICHE ==========

def cohen_d(x, y):
    """Cohen's d effect size: (mean_x - mean_y) / pooled_std"""
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return np.nan
    dof = nx + ny - 2
    pooled_std = np.sqrt(((nx-1)*np.std(x, ddof=1)**2 + (ny-1)*np.std(y, ddof=1)**2) / dof)
    if pooled_std == 0:
        return np.nan
    return (np.mean(x) - np.mean(y)) / pooled_std

def confidence_interval_diff(x, y, confidence=0.95):
    """95% CI for difference of means (x - y)"""
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return np.nan, np.nan
    mean_diff = np.mean(x) - np.mean(y)
    se_diff = np.sqrt(np.var(x, ddof=1)/nx + np.var(y, ddof=1)/ny)
    dof = nx + ny - 2
    t_crit = stats.t.ppf((1 + confidence) / 2, dof)
    margin = t_crit * se_diff
    return mean_diff - margin, mean_diff + margin


def benjamini_hochberg(pvals):
    """Benjamini-Hochberg FDR correction"""
    pvals = np.array(pvals)
    n = len(pvals)
    if n == 0:
        return pvals
    # sort p-values and track original indices
    sorted_idx = np.argsort(pvals)
    sorted_pvals = pvals[sorted_idx]
    # BH correction
    ranks = np.arange(1, n + 1)
    corrected = sorted_pvals * n / ranks
    # ensure monotonicity (reverse cumulative minimum)
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    corrected = np.clip(corrected, 0, 1)
    # restore original order
    original_order = np.argsort(sorted_idx)
    return corrected[original_order]

def compute_statistical_metrics(pairwise_df: pd.DataFrame, marker_columns: List[str]) -> pd.DataFrame:
    """ 
    Function to compute statistical metrics for each marker in the pairwise differences DataFrame.
    """
    
    metrics = []
    # remove the sample id columns if present
    if 'treatment_id' in marker_columns:
        marker_columns.remove('treatment_id')
    if 'control_id' in marker_columns:
        marker_columns.remove('control_id')
        
    for marker in marker_columns:
        # Get difference values (Treatment - Control)
        difference_values = pairwise_df[marker].dropna().values
        zeros = np.zeros_like(difference_values)
        
        # Compute basic metrics
        mean_diff = np.mean(difference_values)
        std_diff = np.std(difference_values, ddof=1)
        
        # Compute absolute mean effect (magnitude of change regardless of direction)
        abs_mean_effect = np.mean(np.abs(difference_values))
        
        # Advanced metrics
        cohen_d_value = cohen_d(difference_values, zeros)
        ci_lower, ci_upper = confidence_interval_diff(difference_values, zeros)
        t_stat, p_value = stats.ttest_rel(difference_values, zeros)
        
        metrics.append({
            'marker': marker,
            'mean_difference': mean_diff,
            'std_difference': std_diff,
            'abs_mean_effect': abs_mean_effect,
            'cohen_d': cohen_d_value,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'p_value': p_value
        })
        
    metrics_df = pd.DataFrame(metrics)
    
    # Apply Benjamini-Hochberg correction
    metrics_df['fdr_corrected'] = benjamini_hochberg(metrics_df['p_value'].values)
    
    # Add significance flag (FDR < 0.05)
    metrics_df['significant_fdr'] = metrics_df['fdr_corrected'] < 0.05
    
    # Add direction classification
    metrics_df['direction'] = metrics_df['mean_difference'].apply(lambda x: 'UP' if x > 0 else 'DOWN')
    
    # Sort by absolute mean effect (magnitude)
    metrics_df = metrics_df.sort_values('abs_mean_effect', ascending=False).reset_index(drop=True)
    
    print(f"✓ Statistics computed for {len(marker_columns)} parameters")
    print(f"✓ Significant parameters (FDR < 0.05): {metrics_df['significant_fdr'].sum()}")
    
    return metrics_df