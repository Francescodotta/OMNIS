import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline


def extract_features(df):
    # Calculate average m/z for each scan
    df['avg_mz'] = df['mzarray'].apply(lambda x: np.mean(x) if isinstance(x, list) else x)
    features = df[['RT', 'avg_mz']]
    return features

def match_peaks(ref_features, sample_features, mz_tolerance=0.01, rt_tolerance=5.0):
    # Sort features by average m/z
    ref_sorted = ref_features.sort_values('avg_mz').reset_index(drop=True)
    sample_sorted = sample_features.sort_values('avg_mz').reset_index(drop=True)
    
    # Use merge_asof for nearest neighbor matching on m/z
    merged = pd.merge_asof(
        left=sample_sorted,
        right=ref_sorted,
        on='avg_mz',
        direction='nearest',
        tolerance=mz_tolerance,
        suffixes=('_sample', '_ref')
    )
    # Drop unmatched peaks
    merged = merged.dropna(subset=['RT_ref'])
    # Calculate RT differences
    rt_diff = np.abs(merged['RT_sample'] - merged['RT_ref'])
    matches = merged[rt_diff <= rt_tolerance]
    return matches[['RT_sample', 'RT_ref']]

def construct_alignment_function(matches):
    if matches.empty:
        return lambda x: x  # No alignment required

    # Calculate rt_shifts
    sample_rts = matches['RT_sample'].values
    rt_shifts = (matches['RT_ref'] - matches['RT_sample']).values

    # Check if rt_shifts are all zeros
    if np.all(rt_shifts == 0):
        return lambda x: x  # No alignment needed

    # Sort and remove duplicates
    matches = matches.sort_values('RT_sample').drop_duplicates(subset='RT_sample')
    sample_rts = matches['RT_sample'].values
    rt_shifts = rt_shifts[np.argsort(sample_rts)]
    sample_rts = np.sort(sample_rts)

    # Ensure sample_rts is strictly increasing
    unique_indices = np.diff(sample_rts) > 0
    sample_rts = sample_rts[np.insert(unique_indices, 0, True)]
    rt_shifts = rt_shifts[np.insert(unique_indices, 0, True)]

    # Fit the spline with a small smoothing factor
    alignment_function = UnivariateSpline(sample_rts, rt_shifts, s=1e-6, k=3)
    return alignment_function

def apply_alignment(df, alignment_function):
    df['RT_aligned'] = df['RT'] + alignment_function(df['RT'])
    return df

def align_chromatograms(reference_json, sample_json_list):
    # Load reference data
    reference_df = pd.read_json(reference_json)
    ref_features = extract_features(reference_df)
    
    aligned_json_list = []
    for sample_json in sample_json_list:
        # Load sample data
        sample_df = pd.read_json(sample_json)
        sample_features = extract_features(sample_df)
        
        # Match peaks and construct alignment function
        matches = match_peaks(ref_features, sample_features)
        alignment_function = construct_alignment_function(matches)
        
        # Apply alignment to sample data
        aligned_df = apply_alignment(sample_df, alignment_function)
        
        # Save aligned data to a new JSON file
        aligned_json_list.append(aligned_df.to_json())
    
    return aligned_json_list
