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


# UTILITY FUNCTIONS
def load_pairs_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Loads paired samples metadata from CSV file.
    
    Expected CSV format:
    control,treatment
    sample1,sample1_treated
    sample2,sample2_treated
    
    Parameters:
    metadata_path (str): Path to CSV file with paired samples.
    
    Returns:
    pd.DataFrame: DataFrame with columns ['control', 'treatment']
    
    Raises:
    ValueError: If CSV is malformed or missing required columns.
    """
    try:
        metadata = pd.read_csv(metadata_path)
    except Exception as e:
        raise ValueError(f"Failed to read metadata CSV: {e}")
    
    # Check for required columns
    required_cols = ['control', 'treatment']
    if not all(col in metadata.columns for col in required_cols):
        raise ValueError(
            f"Metadata CSV must contain columns: {required_cols}. "
            f"Found: {list(metadata.columns)}"
        )
    
    # Remove rows with missing values
    metadata = metadata.dropna(subset=required_cols)
    
    if len(metadata) == 0:
        raise ValueError("No valid pairs found in metadata CSV after removing NaN values")
    
    return metadata


def validate_pairs(df: pd.DataFrame, pairs_metadata: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Validates that paired samples exist in the dataframe and checks for issues.
    
    Parameters:
    df (pd.DataFrame): DataFrame with 'SampleID' column.
    pairs_metadata (pd.DataFrame): DataFrame with 'control' and 'treatment' columns.
    
    Returns:
    tuple: (valid_pairs_df, validation_report)
        - valid_pairs_df: DataFrame with only valid pairs
        - validation_report: Dict with validation statistics
    
    Raises:
    ValueError: If no valid pairs found or critical validation errors.
    """
    available_samples = set(df['SampleID'].unique())
    
    validation_report = {
        'total_pairs_defined': len(pairs_metadata),
        'valid_pairs': 0,
        'missing_controls': [],
        'missing_treatments': [],
        'duplicate_controls': [],
        'duplicate_treatments': [],
        'warnings': []
    }
    
    valid_pairs = []
    
    for idx, row in pairs_metadata.iterrows():
        control = row['control']
        treatment = row['treatment']
        
        is_valid = True
        
        # Check if control exists
        if control not in available_samples:
            validation_report['missing_controls'].append(control)
            is_valid = False
        
        # Check if treatment exists
        if treatment not in available_samples:
            validation_report['missing_treatments'].append(treatment)
            is_valid = False
        
        if is_valid:
            valid_pairs.append({'control': control, 'treatment': treatment})
    
    valid_pairs_df = pd.DataFrame(valid_pairs)
    validation_report['valid_pairs'] = len(valid_pairs_df)
    
    # Check for duplicates (same sample used in multiple pairs)
    if len(valid_pairs_df) > 0:
        control_counts = valid_pairs_df['control'].value_counts()
        treatment_counts = valid_pairs_df['treatment'].value_counts()
        
        duplicated_controls = control_counts[control_counts > 1].index.tolist()
        duplicated_treatments = treatment_counts[treatment_counts > 1].index.tolist()
        
        if duplicated_controls:
            validation_report['duplicate_controls'] = duplicated_controls
            validation_report['warnings'].append(
                f"Warning: {len(duplicated_controls)} control samples used in multiple pairs"
            )
        
        if duplicated_treatments:
            validation_report['duplicate_treatments'] = duplicated_treatments
            validation_report['warnings'].append(
                f"Warning: {len(duplicated_treatments)} treatment samples used in multiple pairs"
            )
    
    # Check if number of pairs is sufficient for statistical analysis
    if validation_report['valid_pairs'] < 3:
        validation_report['warnings'].append(
            f"Warning: Only {validation_report['valid_pairs']} valid pairs found. "
            "Minimum 3 pairs recommended for robust statistical analysis."
        )
    
    # Log validation report
    logger.info(f"Pairs validation: {validation_report['valid_pairs']}/{validation_report['total_pairs_defined']} valid")
    
    if validation_report['missing_controls']:
        logger.warning(f"Missing control samples: {validation_report['missing_controls']}")
    if validation_report['missing_treatments']:
        logger.warning(f"Missing treatment samples: {validation_report['missing_treatments']}")
    
    for warning in validation_report['warnings']:
        logger.warning(warning)
    
    # Raise error if NO valid pairs
    if validation_report['valid_pairs'] == 0:
        error_msg = "No valid pairs found. "
        if validation_report['missing_controls']:
            error_msg += f"Missing controls: {validation_report['missing_controls']}. "
        if validation_report['missing_treatments']:
            error_msg += f"Missing treatments: {validation_report['missing_treatments']}."
        raise ValueError(error_msg)
    
    return valid_pairs_df, validation_report


def extract_parameters(fcs_files):
    """
    Extracts numerical values of parameters from a list of .fcs files and compiles them into a single DataFrame.
    
    Parameters:
    fcs_files (list): List of paths to .fcs files.
    
    Returns:
    pd.DataFrame: DataFrame containing parameter numerical values and sample IDs.
    """
    # define an empty total dataframe
    total_df = pd.DataFrame()
    for fcs_file in fcs_files:
        # read the fcs file
        sample = fk.Sample(fcs_file).as_dataframe(source = "raw")
        # define the sample id 
        sample["SampleID"] = fcs_file.split("/")[-1].replace(".fcs","")
        total_df = pd.concat([total_df, sample], ignore_index=True) 
        
    # retain only the first level of the MultiIndex columns to have a clear dataframe
    total_df.columns = total_df.columns.get_level_values(0)
    
    
def compute_raw_means(fcs_df_concatenated):
    """
    Computes the mean values of parameters from dataframe. 
    
    Parameters:
    fcs_files (list): List of paths to .fcs files.
    
    Returns:
    pd.DataFrame: DataFrame containing mean values of parameters for each sample.
    """
    mean_df = fcs_df_concatenated.groupby('SampleID').mean().reset_index()
    return mean_df     

# standard scale normalization function
def standard_scale_normalization(df):
    """
    Applies standard scale normalization to the dataframe.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing parameter values.
    
    Returns:
    pd.DataFrame: Normalized DataFrame.
    """
    std_scaler = StandardScaler()
    scaled_array = std_scaler.fit_transform(df.select_dtypes(include=['number']))
    scaled_df = pd.DataFrame(scaled_array, columns=df.select_dtypes(include=['number']).columns)
    scaled_df['SampleID'] = df['SampleID'].values
    return scaled_df

# define control-pair treatment
def define_control_pair_treatment(df: pd.DataFrame, metadata_path: str) -> Tuple[pd.DataFrame, List[Tuple[str, str]], Dict]:
    """
    Defines control-treatment pairs based on metadata CSV and validates them.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing parameter values with 'SampleID' column.
    metadata_path (str): Path to CSV file with paired samples.
                         Expected columns: ['control', 'treatment']
    
    Returns:
    tuple: (annotated_df, valid_pairs_list, validation_report)
        - annotated_df: Original df with added 'Condition' column ('control' or 'treatment')
        - valid_pairs_list: List of tuples [(control_id, treatment_id), ...]
        - validation_report: Dict with validation statistics
    
    Raises:
    ValueError: If metadata is invalid or no valid pairs found.
    
    Example:
    >>> metadata.csv:
    control,treatment
    sample1,sample1_800nm
    sample2,sample2_800nm
    
    >>> df_annotated, pairs, report = define_control_pair_treatment(df, "metadata.csv")
    >>> print(pairs)
    [('sample1', 'sample1_800nm'), ('sample2', 'sample2_800nm')]
    """
    # Load and validate metadata
    pairs_metadata = load_pairs_metadata(metadata_path)
    
    # Validate pairs against available samples
    valid_pairs_df, validation_report = validate_pairs(df, pairs_metadata)
    
    # Create sample -> condition mapping
    condition_map = {}
    for _, row in valid_pairs_df.iterrows():
        condition_map[row['control']] = 'control'
        condition_map[row['treatment']] = 'treatment'
    
    # Annotate dataframe with conditions
    df_annotated = df.copy()
    df_annotated['Condition'] = df_annotated['SampleID'].map(condition_map)
    
    # Mark unpaired samples as 'unpaired' (will be excluded from analysis)
    df_annotated['Condition'].fillna('unpaired', inplace=True)
    
    # Convert valid pairs to list of tuples
    valid_pairs_list = [
        (row['control'], row['treatment']) 
        for _, row in valid_pairs_df.iterrows()
    ]

    return df_annotated, valid_pairs_list, validation_report


def remove_outliers_iqr(
    df: pd.DataFrame, 
    multiplier: float = 1.5,
    exclude_cols: List[str] = None
) -> Tuple[pd.DataFrame, List[Dict], int]:
    """
    Removes outliers using the IQR (Interquartile Range) method.
    
    For each parameter (column), values outside [Q1 - k*IQR, Q3 + k*IQR] 
    are removed (set to NaN).
    
    Parameters:
    df (pd.DataFrame): DataFrame with numeric parameters.
    multiplier (float): IQR multiplier. 1.5 (default) is standard, 3.0 is more conservative.
    exclude_cols (List[str]): Columns to exclude from outlier removal (e.g., ['SampleID', 'Condition']).
    
    Returns:
    tuple: (df_cleaned, outlier_info, n_outliers_total)
        - df_cleaned: DataFrame with outliers replaced by NaN
        - outlier_info: List of dicts with outlier statistics per parameter
        - n_outliers_total: Total number of outliers removed
    
    Example:
    >>> df_cleaned, info, n_outliers = remove_outliers_iqr(df, multiplier=1.5, exclude_cols=['SampleID'])
    >>> print(f"Removed {n_outliers} outliers across {len(info)} parameters")
    """
    df_cleaned = df.copy()
    n_outliers_total = 0
    outlier_info = []
    
    # Determine columns to process (exclude non-numeric and specified columns)
    if exclude_cols is None:
        exclude_cols = []
    
    numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns
    cols_to_process = [col for col in numeric_cols if col not in exclude_cols]
        
    for col in cols_to_process:
        Q1 = df_cleaned[col].quantile(0.25)
        Q3 = df_cleaned[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        # Identify outliers
        outliers_mask = (df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)
        n_outliers = outliers_mask.sum()
        
        if n_outliers > 0:
            outlier_info.append({
                'parameter': col,
                'n_outliers': n_outliers,
                'pct_outliers': (n_outliers / len(df_cleaned)) * 100,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'Q1': Q1,
                'Q3': Q3,
                'IQR': IQR
            })
            n_outliers_total += n_outliers
            
            # Remove outliers (set to NaN)
            df_cleaned.loc[outliers_mask, col] = np.nan
    
    
    return df_cleaned, outlier_info, n_outliers_total


def apply_iqr_removal_to_pairs(
    df_normalized: pd.DataFrame,
    valid_pairs_list: List[Tuple[str, str]],
    parameters: List[str],
    multiplier: float = 1.5
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict], int]:
    """
    Applies IQR outlier removal to paired control-treatment samples.
    
    This function pools all control and treatment samples, applies IQR outlier
    removal across the pooled data, then splits back into control and treatment arrays.
    
    Parameters:
    df_normalized (pd.DataFrame): DataFrame with normalized (z-score) sample means.
                                  Must have 'SampleID' as index or column.
    valid_pairs_list (List[Tuple[str, str]]): List of (control_id, treatment_id) tuples.
    parameters (List[str]): List of parameter names (columns) to process.
    multiplier (float): IQR multiplier (default: 1.5).
    
    Returns:
    tuple: (control_df_cleaned, treatment_df_cleaned, outlier_info, n_outliers)
        - control_df_cleaned: DataFrame with control samples (outliers = NaN)
        - treatment_df_cleaned: DataFrame with treatment samples (outliers = NaN)
        - outlier_info: List of dicts with outlier statistics
        - n_outliers: Total number of outliers removed
    
    Example:
    >>> ctrl_clean, treat_clean, info, n_out = apply_iqr_removal_to_pairs(
    ...     df_std, valid_pairs, markers, multiplier=1.5
    ... )
    >>> print(f"Removed {n_out} outliers from {len(valid_pairs)} pairs")
    """
    # Ensure SampleID is in index
    if 'SampleID' in df_normalized.columns:
        df_normalized = df_normalized.set_index('SampleID')
    
    # Collect control and treatment data
    all_controls = []
    all_treatments = []
    
    for control_id, treatment_id in valid_pairs_list:
        all_controls.append(df_normalized.loc[control_id, parameters].values)
        all_treatments.append(df_normalized.loc[treatment_id, parameters].values)
    
    # Create temporary pooled DataFrame (controls + treatments)
    all_data_list = all_controls + all_treatments
    temp_df = pd.DataFrame(all_data_list, columns=parameters)

    
    # Apply IQR outlier removal to pooled data
    temp_df_cleaned, outlier_info, n_outliers = remove_outliers_iqr(
        temp_df, 
        multiplier=multiplier,
        exclude_cols=[]  # No columns to exclude in this case
    )

    
    # Split back into control and treatment arrays
    n_pairs = len(valid_pairs_list)
    control_array_cleaned = temp_df_cleaned.iloc[:n_pairs].values
    treatment_array_cleaned = temp_df_cleaned.iloc[n_pairs:].values
    
    # Create DataFrames for cleaned control and treatment data
    control_ids = [pair[0] for pair in valid_pairs_list]
    treatment_ids = [pair[1] for pair in valid_pairs_list]
    
    control_df_cleaned = pd.DataFrame(
        control_array_cleaned,
        index=control_ids,
        columns=parameters
    )
    
    treatment_df_cleaned = pd.DataFrame(
        treatment_array_cleaned,
        index=treatment_ids,
        columns=parameters
    )


    return control_df_cleaned, treatment_df_cleaned, outlier_info, n_outliers


# compute the paired differences
def compute_paired_differences(
    control_array_cleaned: np.ndarray,
    treatment_array_cleaned: np.ndarray,
    valid_pairs_list: List[Tuple[str, str]],
    parameters: List[str]
) -> Tuple[pd.DataFrame, List[str], Dict]:
    """
    Computes paired differences (treatment - control) for each pair.
    
    This function follows the exact logic from mouse_analysis.ipynb:
    - Calculates difference = treatment - control for each pair
    - Preserves NaN values where outliers were removed
    - Generates meaningful pair names (e.g., "mouse_1_800nm_effect")
    - Tracks valid parameter counts per pair
    
    Parameters:
    control_array_cleaned (np.ndarray): Control data array (n_pairs × n_parameters).
                                        May contain NaN where outliers were removed.
    treatment_array_cleaned (np.ndarray): Treatment data array (n_pairs × n_parameters).
                                          May contain NaN where outliers were removed.
    valid_pairs_list (List[Tuple[str, str]]): List of (control_id, treatment_id) tuples.
    parameters (List[str]): List of parameter names (columns).
    
    Returns:
    tuple: (differences_df, pair_names, metadata)
        - differences_df: DataFrame with paired differences (rows = pairs, cols = parameters)
                         NaN preserved where either control or treatment had outlier
        - pair_names: List of generated pair names
        - metadata: Dict with processing statistics
    
    Raises:
    ValueError: If arrays and pairs list have mismatched lengths.
    
    Example (from notebook):
    >>> # After IQR outlier removal
    >>> diff_df, pair_names, meta = compute_paired_differences(
    ...     control_array_cleaned=control_array_cleaned,  # shape: (4, 45)
    ...     treatment_array_cleaned=treatment_array_cleaned,  # shape: (4, 45)
    ...     valid_pairs_list=[('topo_1', 'topo_1_800nm'), ...],
    ...     parameters=markers
    ... )
    >>> print(f"✓ Matrice differenze shape: {diff_df.shape}")
    >>> print(f"✓ Valori validi: {diff_df.notna().sum().sum()}/{diff_df.size}")
    """
    # Input validation
    n_pairs = len(valid_pairs_list)
    
    if control_array_cleaned.shape[0] != n_pairs:
        raise ValueError(
            f"Control array has {control_array_cleaned.shape[0]} rows but "
            f"{n_pairs} pairs provided"
        )
    
    if treatment_array_cleaned.shape[0] != n_pairs:
        raise ValueError(
            f"Treatment array has {treatment_array_cleaned.shape[0]} rows but "
            f"{n_pairs} pairs provided"
        )
    
    if control_array_cleaned.shape[1] != len(parameters):
        raise ValueError(
            f"Control array has {control_array_cleaned.shape[1]} columns but "
            f"{len(parameters)} parameters provided"
        )
    
    # Initialize containers
    differences_list_cleaned = []
    pair_names = []
    pair_metadata = []
        
    # Iterate through pairs (following notebook logic exactly)
    for i, (control, treatment) in enumerate(valid_pairs_list):
        control_data_clean = control_array_cleaned[i]
        treatment_data_clean = treatment_array_cleaned[i]
        
        # Calcola la differenza (effetto) - NaN se uno dei due è outlier
        difference = treatment_data_clean - control_data_clean
        differences_list_cleaned.append(difference)
        
        # Nome della coppia per il plot (extract meaningful identifier)
        # for pair names use the same name in the sample id without topo example
        pair_name = control
        pair_names.append(pair_name)
        
        
        # Conta quanti valori validi rimangono per questa coppia
        valid_count = np.sum(~np.isnan(difference))
        
        # Store per-pair metadata
        pair_metadata.append({
            'pair_name': pair_name,
            'control_id': control,
            'treatment_id': treatment,
            'n_valid_parameters': int(valid_count),
            'n_total_parameters': len(parameters),
            'pct_valid': (valid_count / len(parameters)) * 100
        })
    
    # Crea DataFrame delle differenze (ora con possibili NaN dove c'erano outlier)
    differences_df = pd.DataFrame(
        differences_list_cleaned, 
        columns=parameters, 
        index=pair_names
    )
    
    # Calculate overall statistics
    n_valid_total = differences_df.notna().sum().sum()
    n_total = differences_df.size
    pct_valid = (n_valid_total / n_total) * 100

    # Compile metadata
    metadata = {
        'n_pairs': n_pairs,
        'n_parameters': len(parameters),
        'n_valid_values': int(n_valid_total),
        'n_total_values': int(n_total),
        'pct_valid_overall': float(pct_valid),
        'pair_details': pair_metadata,
        'mean_difference_overall': float(np.nanmean(differences_df.values)),
        'std_difference_overall': float(np.nanstd(differences_df.values))
    }
    
    # Per-parameter statistics
    param_stats = []
    for param in parameters:
        param_diffs = differences_df[param].values
        n_valid_param = np.sum(~np.isnan(param_diffs))
        
        if n_valid_param > 0:
            param_stats.append({
                'parameter': param,
                'mean_diff': float(np.nanmean(param_diffs)),
                'std_diff': float(np.nanstd(param_diffs)),
                'n_valid': int(n_valid_param),
                'n_pairs': n_pairs,
                'pct_valid': (n_valid_param / n_pairs) * 100
            })
        else:
            param_stats.append({
                'parameter': param,
                'mean_diff': np.nan,
                'std_diff': np.nan,
                'n_valid': 0,
                'n_pairs': n_pairs,
                'pct_valid': 0.0
            })
    
    metadata['parameter_summary'] = param_stats
    
    return differences_df, pair_names, metadata


# calculate statistics
def cohen_d(x,y):
    """Cohen's d effect size: (mean_x - mean_y) / pooled_std"""
    # Rimuovi NaN
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
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
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return np.nan, np.nan
    mean_diff = np.mean(x) - np.mean(y)
    se_diff = np.sqrt(np.var(x, ddof=1)/nx + np.var(y, ddof=1)/ny)
    dof = nx + ny - 2
    t_crit = t.ppf((1 + confidence) / 2, dof)
    margin = t_crit * se_diff
    return mean_diff - margin, mean_diff + margin



def benjamini_hochberg(pvals):
    """Benjamini-Hochberg FDR correction"""
    pvals = np.array(pvals)
    # Remove NaN
    valid_mask = ~np.isnan(pvals)
    if valid_mask.sum() == 0:
        return pvals
    
    n = valid_mask.sum()
    corrected = np.full_like(pvals, np.nan)
    
    valid_pvals = pvals[valid_mask]
    sorted_idx = np.argsort(valid_pvals)
    sorted_pvals = valid_pvals[sorted_idx]
    
    ranks = np.arange(1, n + 1)
    corrected_sorted = sorted_pvals * n / ranks
    corrected_sorted = np.minimum.accumulate(corrected_sorted[::-1])[::-1]
    corrected_sorted = np.clip(corrected_sorted, 0, 1)
    
    original_order = np.argsort(sorted_idx)
    corrected[valid_mask] = corrected_sorted[original_order]
    
    return corrected



# calculate statistics for each parameter
def calculate_statistics(df: pd.DataFrame, differences_df: pd.DataFrame, control_ids: List[str], treatment_ids: List[str]) -> pd.DataFrame:
    """
    Calculates statistics for each parameter comparing control and treatment groups.
    
    Parameters:
    df (pd.DataFrame): DataFrame with parameter differences (rows = pairs, cols = parameters).
    control_ids (List[str]): List of control sample IDs.
    treatment_ids (List[str]): List of treatment sample IDs.
    
    Returns:
    pd.DataFrame: DataFrame with statistics for each parameter.
    """
    
    markers = list(df.columns)
    effect_sizes = []
    ci_lower = []
    ci_upper = []
    pvals = []
    
    for i in range (len(markers)):
        if markers[i] == 'SampleID':
            markers.pop(i)
            break
        control_values = df.loc[control_ids, markers[i]].values
        treatment_values = df.loc[treatment_ids, markers[i]].values
        
        # Effect size (Cohen's d)
        d = cohen_d(treatment_values, control_values)
        effect_sizes.append(d)
        
        # 95% Confidence Interval
        ci_low, ci_up = confidence_interval_diff(treatment_values, control_values)
        ci_lower.append(ci_low)
        ci_upper.append(ci_up)
        
        # Paired t-test
        valid_mask = ~np.isnan(control_values) & ~np.isnan(treatment_values)
        if valid_mask.sum() >= 2:
            _, p = stats.ttest_rel(treatment_values[valid_mask], control_values[valid_mask])
            pvals.append(p)
        else:
            pvals.append(np.nan)
        
    stats_df = pd.DataFrame({
        'Parameter': markers,
        'mean_difference': df[markers].mean(axis=0).values,
        'std_difference': df[markers].std(axis=0).values,
        'Cohen_d': effect_sizes,
        'CI_Lower': ci_lower,
        'CI_Upper': ci_upper,
        'p_value': pvals,
        'fdr_corrected_p': benjamini_hochberg(pvals),
        'abs_mean_effect': differences_df.abs().mean(axis=0).values
    })
    
    # significance fdr
    significance = []
    for p in stats_df['fdr_corrected_p']:
        if np.isnan(p):
            significance.append('Not Significant')
        elif p < 0.05:
            significance.append('Significant')
        else:
            significance.append('Not Significant')
    stats_df['Significance'] = significance
    # directionality
    directionality = []
    for mean_diff in stats_df['mean_difference']:
        if mean_diff > 0:
            directionality.append('Up in Treatment')
        elif mean_diff < 0:
            directionality.append('Down in Treatment')
        else:
            directionality.append('No Change')
    stats_df['Directionality'] = directionality
    return stats_df

# generate visualization 
def volcano_plot(df_stats: pd.DataFrame, output_path: str):
    """
    Generates a volcano plot from statistics DataFrame.
    
    Parameters:
    df_stats (pd.DataFrame): DataFrame with statistics for each parameter.
    output_path (str): Path to save the volcano plot image.
    """
    plt.figure(figsize=(10, 8))
    
    # Scatter plot
    plt.scatter(
        df_stats['mean_difference'], 
        -np.log10(df_stats['p_value']), 
        c=df_stats['Significance'].map({'Significant': 'red', 'Not Significant': 'grey'}),
        alpha=0.7
    )
    
    # Add labels and title
    plt.title('Volcano Plot')
    plt.xlabel('Mean Difference (Treatment - Control)')
    plt.ylabel('-Log10(p-value)')
    
    # Add horizontal line for significance threshold
    plt.axhline(-np.log10(0.05), color='blue', linestyle='--', label='p = 0.05')
    
    plt.legend()
    plt.grid(True)
    
    # Save plot
    plt.savefig(output_path, dpi=600)
    plt.close()
    
# heatmap plot
def heatmap_plot(differences_df: pd.DataFrame, output_path: str):
    """
    Generates a heatmap plot from differences DataFrame.
    
    Parameters:
    differences_df (pd.DataFrame): DataFrame with paired differences (rows = pairs, cols = parameters).
    output_path (str): Path to save the heatmap plot image.
    """
    import seaborn as sns
    
    plt.figure(figsize=(12, 10))
    
    # Create heatmap
    sns.heatmap(
        differences_df,
        cmap='bwr',
        center=0,
        cbar_kws={'label': 'Difference (Treatment - Control)'},
        annot=False
    )
    
    # Add labels and title
    plt.title('Heatmap of Paired Differences')
    plt.xlabel('Parameters')
    plt.ylabel('Pairs')
    
    # Save plot
    plt.savefig(output_path, dpi=600)
    plt.close()
    
# 2 heatmaps for all down and up regulated markers in 100% of the pairs
def heatmap_up_down_plots(differences_df:pd.DataFrame, output_dir: str, dpi:int =300, min_figsize:int = 12, figsize_per_param:float=0.4) -> Tuple[Dict, Dict]:
    """
    Generates two heatmaps for parameters with 100% consistent UP or DOWN regulation.
    
    This function:
    1. Identifies parameters where ALL pairs show the same direction (all > 0, all < 0)
    2. Creates separate heatmaps for 100% up-regulated and 100% down-regulated parameters
    3. Uses appropriate color scales (REDS FOR UP, BLUE FOR DOWN)
    4. Saves high resolution plots to specified directory. 
    
    Parameters:
    differences_df (pd.DataFrame): DataFrame with paired differences (rows=pairs, cols=parameters). NaN values indicate outliers removed
    output_dir (string): Directory path to save heatmap images.
    dpi (int): Resolution for saved images (default: 300)    
    
    Returns:
    tuple: (up_status, down_status)
        -up_stats: Dict with statistics about 100% up-regulated parameters
        -down_stats: Dict with statistics about 100% down-regulated parameters.
        
    Raises:
    ValueError: if output_dir doesn't exist or differences_df is empty.
    """
    
    # validate inputs
    if differences_df.empty:
        raise ValueError("dataframe of the differences is empty")
    # create output dir
    if not os.path.exist(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    n_samples = len(differences_df)
    
    # CONSISTENCY ANALYSIS
    consistency_analysis = []
    for param in differences_df.columns:
        param_values = differences_df[param].dropna()
        n_valid = len(param_values)

        if n_valid > 0:
            n_positive = (param_values > 0).sum()
            n_negative = (param_values < 0).sum()
            mean_val = param_values.mean()
            
            # Determine if it's 100% consistent
            is_100_up= (n_positive == n_valid) and (n_negative == 0)
            is_100_down = (n_negative == n_valid) and (n_positive == 0)
            
            consistency_analysis.append({'parameter': param, 'n_valid':n_valid, 'n_positive':n_positive, 'n_negative': n_negative,
                'mean_diff': mean_val, 'min_diff': param_values.min(),
                'max_diff': param_values.max(),
                'consistency_pct': max(n_positive, n_negative)/n_valid*100, 'is_100_up':is_100_up, 'is_100_down': is_100_down, 'direction': 'UP' if mean_val > 0 else 'DOWN'})
            
    consistency_df = pd.DataFrame(consistency_analysis)
    # Filter 100% consistent parameters
    params_100_up = consistency_df[consistency_df['is_100_up']].sort_values('mean_diff', ascending=False)
    params_100_down = consistency_df[consistency_df['is_100_down']].sort_values('mean_diff', ascending=True)
    ## HEATMAP 100% UP REGULATED
    up_stats = {
        'n_parameters': len(params_100_up),
        'parameters': list(params_100_up['parameter'].values) if len(params_100_up)>0 else [],
        'mean_range': (float(params_100_up['mean_diff'].min()), float(params_100_up['mean_diff'].max())) if len(params_100_up) > 0 else (np.nan, np.nan),
        'plot_saved':False,
        'plot_path': None
    }
    # if the 100% params are up-regulated
    if len(params_100_up) > 0:
        up_100_diff = differences_df[params_100_up['parameter'].values]
        # use scale from 0 since they are all positive values
        vmin_up = 0
        vmax_up = np.nanmax(up_100_diff.values)
        # Calculate the best figure size
        n_up = len(params_100_up)
        fig_width = max(min_figsize, n_up*figsize_per_param)    

        # create heatmap with reds color map
        fig, ax = plt.subplots(1,1, figsize = (fig_width, 6))
        sns.heatmap(up_100_diff,
            ax = ax,
            cmap = 'Reds',
            vmin = vmin_up,
            vmax = vmax_up,
            cbar_kws={'label': 'Difference (Treatment vs Control) [z-score]'},
            linewidths=0.5,
            annot=False,
            mask=up_100_diff.isna())
        ax.set_title(f"100% UP-regulated paramters (n={n_up})\n" f"All {n_samples} sample pairs show INCREASE", fontsize = 15, fontweight='bold', color='darkred')
        ax.set_xlabel("Parameters (100% Increased in ALL samples)", fontsize=13)
        ax.set_ylabel("Sample Pairs", fontsize=13)
        
        plt.xticks(rotation=45, ha='right', fontsize = 11)
        plt.yticks(rotation=0, fontsize = 11)
        plt.tight_layout()
        # SAVE PLOT
        output_path_up = os.path.join(output_dir, 'heatmap_100pctUP_regulated.png')
        fig.savefig(output_path_up, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        
        # save the results within the dict
        up_stats['plot_saved']=True
        up_stats['plot_path'] = output_path_up
        
        ### HEATMAP FOR PARAMETERS THAT ARE 100% DOWN
        down_stats = {'n_parameters':len(params_100_down), 
                    'parameters':list(params_100_down['parameter'].values) if len(params_100_down) > 0 else [],
                    'mean_range': (float(params_100_down['mean_diff'].min()), float(params_100_down['mean_diff'].max())) if len(params_100_down) > 0 else (np.nan, np.nan),
                    'plot_saved': False,
                    'plot_path': None
                    }

    
    # check that the downregulated parameters exist
    if len(params_100_down) > 0:
        down_100_diff = differences_df[params_100_down['parameter'].values]
        # uses scale that arrives at zero
        vmin_down = np.namin(down_100_diff.values)
        vmax_down = 0
        n_down = len(params_100_down)
        fig_width = max(min_figsize, figsize_per_param*n_down)
        
        # create heatmaps with blues_r colormap
        fig, ax= plt.subplots(1,1,figsize = (fig_width, 6))
        sns.heatmap(down_100_diff, ax=ax, cmap='Blues_r', vmin=vmin_down, vmax=vmax_down, 
                    cbar_kws={'label':'Difference (Treatment-Control)[z-score]'},
                    linewidths=0.5, annot=False, mask=down_100_diff.isna()
                    )
        ax.set_title(f"100% DOWN regulated Parameters (n={n_down}) \n" f"All {n_samples} sample pairs show DECREASE",
                     fontsize = 15, fontweight='bold', color='darkblue'
                     )
        ax.set_xlabel("Parameters (100% decreased in ALL Samples)", fontsize =13)
        ax.set_ylabel('Sample Pairs', fontsize= 13)
        
        plt.xticks(rotation=45, ha='right', fontsize = 12)
        plt.yticks(rotation=0, fontsize=12)
        
        plt.tight_layout()
        output_path_down = os.path.join(output_dir, "heatmap_100pct_DOWN_regulated.png")
        fig.savefig(output_path_down, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        down_stats['plot_saved'] = True
        down_stats['plot_path']=output_path_down
        
    ## EXPORT CONSISTENCY ANALYSIS
        
    return up_stats, down_stats