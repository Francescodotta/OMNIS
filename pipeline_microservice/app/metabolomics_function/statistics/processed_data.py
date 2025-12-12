import pandas as pd
from scipy import stats
from scipy.stats import ttest_ind
import numpy as np
import matplotlib.pyplot as plt


# load the excel matrix data
def read_processed_matrix(file_path: str) -> pd.DataFrame:
    """
    Reads an Excel file containing metabolomics data and returns a processed DataFrame.
    
    Args:
        file_path (str): Path to the Excel file.

    Returns:
        pd.DataFrame: Processed DataFrame containing metabolomics data.
    """
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.lower()

    if 'label' not in df.columns:
        print(df.columns)
        raise ValueError("The provided Excel file does not contain a 'label' column.")
    # Split the dataframe into groups based on the 'label' column
    group1 = df[df['label'] == 0].drop(columns=['label'])
    group2 = df[df['label'] == 1].drop(columns=['label'])

    # Process the data as needed
    return group1, group2

# raw mean function
def calculate_statistics(group1: pd.DataFrame, group2: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the mean values for each group.

    Args:
        group1 (pd.DataFrame): DataFrame for group 1.
        group2 (pd.DataFrame): DataFrame for group 2.

    Returns:
        pd.DataFrame: DataFrame containing the mean values for each group.
    """
    statistical_results = []
    # remove name column if present
    if 'name' in group1.columns:
        group1 = group1.drop(columns=['name'])
    if 'name' in group2.columns:
        group2 = group2.drop(columns=['name'])
    # Itera su ogni metabolita
    for metabolite in group1.columns:
        # Estrai i dati del metabolita dai due gruppi
        values_group0 = group1[metabolite].dropna()
        values_group1 = group2[metabolite].dropna()

        
        # === MEDIE ===
        mean_0 = values_group0.mean()
        mean_1 = values_group1.mean()

        # === FOLD CHANGE (log2) ===
    # log2(media_casi_gravi / media_controlli)
        epsilon = 1e-10  # evita divisione per zero
        log2fc = np.log2((mean_0 + epsilon) / (mean_1 + epsilon))
        
        # === T-TEST (significatività statistica) ===
        t_stat, p_value = ttest_ind(values_group0, values_group1, equal_var=False)
        
        # Evita log(0)
        if p_value == 0:
            p_value = 1e-300
        
        # === SALVA RISULTATI ===
        statistical_results.append({
            'Metabolite': metabolite,
            'Mean_Group0': mean_0,
            'Mean_Group1': mean_1,
            'Log2FC': log2fc,
            'P_Value': p_value,
            'Neg_Log10_P': -np.log10(p_value),
            'T_Statistic': t_stat
        })
    df_stats = pd.DataFrame(statistical_results)
    return df_stats



# generate volcano plot data
def generate_volcano_data(statistical_results: pd.DataFrame, p_value_threshold: float = 0.05, log2fc_threshold: float = 1.0) -> pd.DataFrame:
    """
    Generate data for volcano plot based on statistical results.

    Args:
        statistical_results (pd.DataFrame): DataFrame containing statistical results.
        p_value_threshold (float): Threshold for p-value significance.
        log2fc_threshold (float): Threshold for log2 fold change significance.

    Returns:
        pd.DataFrame: DataFrame with volcano plot data.
    """
    volcano_data = statistical_results.copy()
    # Aggiungi una colonna per indicare la significatività
    volcano_data['Significant'] = (
        (volcano_data['P_Value'] < p_value_threshold) & 
        (np.abs(volcano_data['Log2FC']) >= log2fc_threshold)
    )
    return volcano_data

# save volcano plot to png
def save_volcano_plot(volcano_data: pd.DataFrame, output_path: str):
    """
    Save a volcano plot as a PNG file.

    Args:
        volcano_data (pd.DataFrame): DataFrame containing volcano plot data.
        output_path (str): Path to save the PNG file.
    """
    plt.figure(figsize=(10, 8))
    # Plot non-significant points
    plt.scatter(
        volcano_data[~volcano_data['Significant']]['Log2FC'], 
        volcano_data[~volcano_data['Significant']]['Neg_Log10_P'], 
        color='grey', alpha=0.5, label='Not Significant'
    )
    # Plot significant points
    plt.scatter(
        volcano_data[volcano_data['Significant']]['Log2FC'], 
        volcano_data[volcano_data['Significant']]['Neg_Log10_P'], 
        color='red', alpha=0.7, label='Significant'
    )
    plt.axhline(-np.log10(0.05), color='blue', linestyle='--', label='p-value = 0.05')
    plt.axvline(1.0, color='green', linestyle='--', label='Log2FC = 1')
    plt.axvline(-1.0, color='green', linestyle='--')
    plt.title('Volcano Plot')
    plt.xlabel('Log2 Fold Change')
    plt.ylabel('-Log10 P-Value')
    plt.legend()
    plt.savefig(output_path)
    plt.close()