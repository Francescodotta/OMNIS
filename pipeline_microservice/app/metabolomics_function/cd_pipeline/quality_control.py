"""
Quality Control Module for LC-MS Metabolomics Data

This module provides comprehensive quality control functions for LC-MS metabolomics data
processed with OpenMS. It calculates metrics, generates visualizations, and produces reports
that help assess the quality and reproducibility of the data.

Key features:
- Feature-level metrics for individual samples
- Cross-sample comparison and consensus map analysis
- Automatic QC sample detection
- Relative Standard Deviation (RSD) calculation for QC samples
- Visualization of key quality indicators
- PDF report generation
- File-based results storage for later integration with other systems

The module requires:
- pyopenms for reading featureXML/consensusXML files
- numpy/pandas for numerical processing
- matplotlib/seaborn for visualization
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
import json

try:
    import pyopenms as oms
except ImportError:
    oms = None


def load_feature_map_metrics(fxml_path):
    """
    Extract comprehensive metrics from a single featureXML file.
    
    This function loads a featureXML file and calculates various metrics that
    describe the feature detection quality, including:
    - Feature count (total number of detected features)
    - Total Ion Current (TIC) - sum of all feature intensities
    - Intensity distribution statistics (mean, median, std)
    - m/z range and distribution
    - Retention time (RT) range and distribution
    - Charge state distribution
    - Peak width statistics
    
    Parameters
    ----------
    fxml_path : str
        Path to the featureXML file
        
    Returns
    -------
    dict
        Dictionary containing calculated metrics and raw data
    """
    if oms is None:
        raise ImportError("pyopenms is required for QC analysis")
    
    # Load feature map using PyOpenMS
    fmap = oms.FeatureMap()
    oms.FeatureXMLFile().load(fxml_path, fmap)
    
    # Initialize basic metrics dictionary
    metrics = {
        'feature_count': fmap.size(),
        'file_path': fxml_path,
        'file_name': os.path.basename(fxml_path)
    }
    
    # Initialize arrays for feature properties
    intensities = []  # Feature intensities
    mzs = []          # Feature m/z values
    rts = []          # Feature retention times
    charges = []      # Feature charge states
    widths = []       # Feature chromatographic peak widths
    
    # Extract feature-level information
    for feat in fmap:
        try:
            # Extract basic properties
            intensities.append(float(feat.getIntensity()))
            mzs.append(float(feat.getMZ()))
            rts.append(float(feat.getRT()))
            charges.append(feat.getCharge())
            
            # Calculate retention time width from the feature's convex hull (peak shape)
            hull = feat.getConvexHull()
            if hull.getBoundingBox().isEmpty():
                widths.append(None)  # No valid peak shape
            else:
                widths.append(hull.getBoundingBox().width())  # RT width in seconds
        except Exception:
            # Skip problematic features to ensure robustness
            continue
    
    # Calculate summary statistics
    metrics['TIC'] = float(np.sum(intensities)) if intensities else 0
    metrics['intensity_mean'] = float(np.mean(intensities)) if intensities else None
    metrics['intensity_median'] = float(np.median(intensities)) if intensities else None
    metrics['intensity_std'] = float(np.std(intensities)) if intensities else None
    metrics['mz_range'] = [float(min(mzs)), float(max(mzs))] if mzs else [None, None]
    metrics['rt_range'] = [float(min(rts)), float(max(rts))] if rts else [None, None]
    metrics['rt_mean'] = float(np.mean(rts)) if rts else None
    
    # Count features by charge state
    metrics['charge_distribution'] = dict(pd.Series(charges).value_counts().to_dict())
    
    # Calculate mean peak width (excluding None values)
    metrics['peak_width_mean'] = float(np.nanmean(widths)) if widths and not all(w is None for w in widths) else None
    
    # Store raw data arrays for further processing
    metrics['_intensities'] = intensities
    metrics['_mzs'] = mzs
    metrics['_rts'] = rts
    
    return metrics


def load_consensus_map_metrics(consensus_path):
    """
    Extract metrics from a consensusXML file containing aligned features across samples.
    
    A consensus map links corresponding features across multiple samples, providing
    a matrix of feature intensities with rows representing consensus features and
    columns representing individual samples.
    
    Parameters
    ----------
    consensus_path : str
        Path to the consensusXML file
        
    Returns
    -------
    tuple
        A tuple containing:
        - metrics (dict): Dictionary of calculated metrics
        - sample_names (list): List of sample names extracted from the consensus map
        - intensity_matrix (numpy.ndarray): 2D matrix of feature intensities [features × samples]
    """
    if oms is None:
        raise ImportError("pyopenms is required for QC analysis")
    
    # Load consensus map using PyOpenMS
    cmap = oms.ConsensusMap()
    oms.ConsensusXMLFile().load(consensus_path, cmap)
    
    # Extract sample information from column headers
    headers = cmap.getColumnHeaders()
    sample_names = [os.path.basename(headers[i].getFilename()) for i in range(len(headers))]
    
    # Initialize basic metrics
    metrics = {
        'feature_count': cmap.size(),
        'file_path': consensus_path,
        'file_name': os.path.basename(consensus_path),
        'sample_count': len(sample_names),
        'samples': sample_names
    }
    
    # Create intensity matrix [features × samples]
    intensity_matrix = np.zeros((cmap.size(), len(sample_names)))
    
    # Extract feature data
    consensus_mzs = []  # Consensus m/z values
    consensus_rts = []  # Consensus retention times
    
    # Fill intensity matrix and collect feature properties
    for i, cf in enumerate(cmap):
        consensus_mzs.append(float(cf.getMZ()))
        consensus_rts.append(float(cf.getRT()))
        
        # Usa getFeatureHandles() invece di getElements()
        handles = cf.getFeatureHandles()
        for handle in handles:
            idx = handle.getMapIndex()  # Sample index
            intensity_matrix[i, idx] = float(handle.getIntensity())
    
    # Calculate feature presence statistics (how many samples contain each feature)
    feature_presence = np.sum(intensity_matrix > 0, axis=1)
    
    # Store feature presence metrics
    metrics['mz_range'] = [float(min(consensus_mzs)), float(max(consensus_mzs))] if consensus_mzs else [None, None]
    metrics['rt_range'] = [float(min(consensus_rts)), float(max(consensus_rts))] if consensus_rts else [None, None]
    metrics['feature_presence'] = {
        'mean': float(np.mean(feature_presence)),
        'median': float(np.median(feature_presence)),
        'complete': int(np.sum(feature_presence == len(sample_names))),  # Features present in all samples
        'missing_values_pct': float(np.sum(intensity_matrix == 0) / intensity_matrix.size * 100)  # % of zeros
    }
    
    # Store raw data for further processing
    metrics['_intensity_matrix'] = intensity_matrix
    metrics['_consensus_mzs'] = consensus_mzs
    metrics['_consensus_rts'] = consensus_rts
    
    return metrics, sample_names, intensity_matrix


def detect_qc_samples(sample_names, qc_pattern="QC"):
    """
    Identify Quality Control (QC) samples based on their names.
    
    Parameters
    ----------
    sample_names : list
        List of sample names (file names)
    qc_pattern : str, default="QC"
        Pattern to match in sample names to identify QC samples
        
    Returns
    -------
    list
        List of indices corresponding to QC samples in the original list
    """
    qc_indices = []
    
    # Search for the QC pattern in each sample name (case-insensitive)
    for i, name in enumerate(sample_names):
        if qc_pattern.lower() in name.lower():
            qc_indices.append(i)
    
    return qc_indices


def calculate_qc_metrics(intensity_matrix, qc_indices):
    """
    Calculate Relative Standard Deviation (RSD) metrics for QC samples.
    
    RSD (also known as CV - Coefficient of Variation) is a critical quality metric
    for metabolomics data. Lower RSDs indicate better reproducibility.
    
    Parameters
    ----------
    intensity_matrix : numpy.ndarray
        2D matrix of feature intensities [features × samples]
    qc_indices : list
        List of indices corresponding to QC samples
        
    Returns
    -------
    tuple or None
        If QC samples are found:
            - qc_metrics (dict): Dictionary of QC metrics
            - rsd (numpy.ndarray): Array of RSD values for each feature
        If no QC samples are found:
            - None
    """
    # Return None if no QC samples are found
    if not qc_indices:
        return None, None
    
    # Extract intensities for QC samples only
    qc_matrix = intensity_matrix[:, qc_indices]
    
    # Replace zeros with NaN (treat as missing values)
    qc_matrix = np.where(qc_matrix > 0, qc_matrix, np.nan)
    
    # Calculate mean and standard deviation for each feature across QC samples
    means = np.nanmean(qc_matrix, axis=1)  # Mean per feature (row)
    stds = np.nanstd(qc_matrix, axis=1)    # Std dev per feature (row)
    
    # Calculate RSD (CV) in percentage: (std / mean) * 100
    rsd = stds / means * 100
    
    # Filter valid RSDs (non-NaN)
    valid_rsd = rsd[~np.isnan(rsd)]
    
    # Calculate QC metrics
    qc_metrics = {
        'rsd_mean': float(np.nanmean(rsd)),           # Mean RSD across all features
        'rsd_median': float(np.nanmedian(rsd)),       # Median RSD (more robust to outliers)
        'rsd_std': float(np.nanstd(rsd)),             # Standard deviation of RSDs
        'features_below_20rsd': int(np.sum(rsd < 20)),  # Count of features with RSD < 20%
        'features_below_30rsd': int(np.sum(rsd < 30)),  # Count of features with RSD < 30%
        'features_below_20rsd_pct': float(np.sum(rsd < 20) / len(valid_rsd) * 100),  # % features with RSD < 20%
        'features_below_30rsd_pct': float(np.sum(rsd < 30) / len(valid_rsd) * 100),  # % features with RSD < 30%
        'total_features_with_rsd': int(len(valid_rsd))  # Total number of features with valid RSD
    }
    
    return qc_metrics, rsd


def plot_feature_intensity_distributions(feature_metrics, output_path):
    """
    Generate plots showing Total Ion Current (TIC) and feature count distributions across samples.
    
    Parameters
    ----------
    feature_metrics : list
        List of dictionaries containing metrics for each sample
    output_path : str
        Path to save the output plot
        
    Returns
    -------
    str
        Path to the saved plot file
    """
    # Create a figure with two subplots
    plt.figure(figsize=(10, 6))
    
    # Extract sample names and metrics
    sample_names = [m['file_name'] for m in feature_metrics]
    tics = [m['TIC'] for m in feature_metrics]
    
    # Create TIC bar plot (left panel)
    plt.subplot(1, 2, 1)
    sns.barplot(x=range(len(sample_names)), y=tics)
    plt.xticks(range(len(sample_names)), sample_names, rotation=45, ha='right')
    plt.title('Total Ion Current (TIC)')
    plt.tight_layout()
    
    # Create feature count bar plot (right panel)
    plt.subplot(1, 2, 2)
    feature_counts = [m['feature_count'] for m in feature_metrics]
    sns.barplot(x=range(len(sample_names)), y=feature_counts)
    plt.xticks(range(len(sample_names)), sample_names, rotation=45, ha='right')
    plt.title('Feature Count')
    
    # Ensure proper layout and save the plot
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    
    return output_path


def plot_intensity_boxplot(intensity_matrix, sample_names, output_path):
    """
    Generate boxplot of log-transformed intensities across samples.
    
    Parameters
    ----------
    intensity_matrix : numpy.ndarray
        2D matrix of feature intensities [features × samples]
    sample_names : list
        List of sample names corresponding to columns in intensity_matrix
    output_path : str
        Path to save the output plot
        
    Returns
    -------
    str
        Path to the saved plot file
    """
    # Create figure
    plt.figure(figsize=(12, 6))
    
    # Convert to dataframe for easier plotting with seaborn
    # Apply log10 transformation to intensities, replacing zeros with NaN
    df = pd.DataFrame(np.log10(np.where(intensity_matrix > 0, intensity_matrix, np.nan)), 
                     columns=sample_names)
    
    # Create boxplot
    sns.boxplot(data=df)
    plt.xticks(rotation=45, ha='right')
    plt.title('Log10 Intensity Distribution')
    plt.ylabel('Log10(Intensity)')
    plt.tight_layout()
    
    # Save and close
    plt.savefig(output_path)
    plt.close()
    
    return output_path


def plot_rsd_histogram(rsd, output_path):
    """
    Generate histogram of Relative Standard Deviation (RSD) values from QC samples.
    
    Parameters
    ----------
    rsd : numpy.ndarray
        Array of RSD values for each feature
    output_path : str
        Path to save the output plot
        
    Returns
    -------
    str or None
        Path to the saved plot file, or None if no valid RSD values are available
    """
    if rsd is None or len(rsd) == 0:
        return None
    
    plt.figure(figsize=(8, 6))
    
    # Filter out NaNs and extreme values for better visualization
    valid_rsd = rsd[~np.isnan(rsd)]       # Remove NaN values
    valid_rsd = valid_rsd[valid_rsd < 100]  # Limit to reasonable range (0-100%)
    
    # Create histogram with kernel density estimate
    sns.histplot(valid_rsd, bins=30, kde=True)
    
    # Add reference lines for common QC thresholds
    plt.axvline(x=20, color='red', linestyle='--', label='20% RSD')
    plt.axvline(x=30, color='orange', linestyle='--', label='30% RSD')
    
    # Add labels and legend
    plt.title('Relative Standard Deviation (RSD) Distribution in QC Samples')
    plt.xlabel('RSD (%)')
    plt.ylabel('Feature Count')
    plt.legend()
    plt.tight_layout()
    
    # Save and close
    plt.savefig(output_path)
    plt.close()
    
    return output_path


def plot_rt_mz_distribution(feature_metrics, output_path):
    """
    Plot retention time (RT) and m/z distributions for all samples.
    
    Parameters
    ----------
    feature_metrics : list
        List of dictionaries containing metrics for each sample
    output_path : str
        Path to save the output plot
        
    Returns
    -------
    str
        Path to the saved plot file
    """
    plt.figure(figsize=(12, 6))
    
    # RT distribution (left panel)
    plt.subplot(1, 2, 1)
    for i, metrics in enumerate(feature_metrics):
        if metrics['_rts']:
            # Create kernel density estimation for RT
            sns.kdeplot(metrics['_rts'], label=metrics['file_name'])
    
    plt.title('RT Distribution')
    plt.xlabel('Retention Time (s)')
    plt.ylabel('Density')
    plt.legend()
    
    # m/z distribution (right panel)
    plt.subplot(1, 2, 2)
    for i, metrics in enumerate(feature_metrics):
        if metrics['_mzs']:
            # Create kernel density estimation for m/z
            sns.kdeplot(metrics['_mzs'], label=metrics['file_name'])
    
    plt.title('m/z Distribution')
    plt.xlabel('m/z')
    plt.ylabel('Density')
    plt.legend()
    
    # Ensure proper layout and save
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    
    return output_path


def plot_rt_mz_scatter(consensus_metrics, output_path):
    """
    Plot retention time (RT) vs m/z scatter plot colored by intensity.
    
    Parameters
    ----------
    consensus_metrics : dict
        Dictionary containing consensus map metrics
    output_path : str
        Path to save the output plot
        
    Returns
    -------
    str or None
        Path to the saved plot file, or None if no valid data is available
    """
    # Check for required data
    if not consensus_metrics['_consensus_mzs'] or not consensus_metrics['_consensus_rts']:
        return None
    
    plt.figure(figsize=(10, 8))
    
    # Calculate mean intensity per feature (across samples)
    # Replace zeros with NaN, calculate mean, then log-transform
    mean_intensities = np.log10(np.nanmean(np.where(
        consensus_metrics['_intensity_matrix'] > 0, 
        consensus_metrics['_intensity_matrix'], 
        np.nan), axis=1))
    
    # Create scatter plot with RT on x-axis, m/z on y-axis, colored by mean intensity
    plt.scatter(consensus_metrics['_consensus_rts'], 
               consensus_metrics['_consensus_mzs'],
               c=mean_intensities, 
               cmap='viridis',  # Color map for intensity
               alpha=0.6,       # Transparency
               s=20)            # Point size
    
    # Add color bar
    plt.colorbar(label='Log10(Mean Intensity)')
    
    # Add labels and title
    plt.title('Feature Map: RT vs m/z')
    plt.xlabel('Retention Time (s)')
    plt.ylabel('m/z')
    plt.tight_layout()
    
    # Save and close
    plt.savefig(output_path)
    plt.close()
    
    return output_path


def generate_qc_report(feature_metrics, consensus_metrics, qc_metrics, plots, output_path):
    """
    Generate a comprehensive PDF report with all QC information.
    
    Parameters
    ----------
    feature_metrics : list
        List of dictionaries containing metrics for each sample
    consensus_metrics : dict
        Dictionary containing consensus map metrics
    qc_metrics : dict or None
        Dictionary containing QC metrics, or None if QC samples weren't found
    plots : list
        List of paths to generated plot files
    output_path : str
        Path to save the output PDF report
        
    Returns
    -------
    str
        Path to the saved PDF report
    """
    with PdfPages(output_path) as pdf:
        # Title page
        plt.figure(figsize=(12, 8))
        plt.axis('off')
        plt.text(0.5, 0.6, "Metabolomics Quality Control Report", 
                ha='center', fontsize=24, fontweight='bold')
        plt.text(0.5, 0.5, f"Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                ha='center', fontsize=14)
        plt.text(0.5, 0.4, "OMNIS Platform", ha='center', fontsize=16)
        pdf.savefig()
        plt.close()
        
        # Sample summary page
        plt.figure(figsize=(12, 8))
        plt.axis('off')
        plt.text(0.5, 0.95, "Sample Summary", ha='center', fontsize=18, fontweight='bold')
        
        # Build summary text
        text = "Samples processed:\n"
        for i, metrics in enumerate(feature_metrics):
            text += f"  {i+1}. {metrics['file_name']} - {metrics['feature_count']} features\n"
        
        # Gestisci il caso in cui consensus_metrics potrebbe essere None o avere feature_count=0
        if consensus_metrics and consensus_metrics.get('feature_count', 0) > 0:
            complete_pct = (consensus_metrics['feature_presence']['complete'] / consensus_metrics['feature_count'] * 100)
            text += f"\nConsensus map: {consensus_metrics['feature_count']} features across {consensus_metrics['sample_count']} samples\n"
            text += f"Missing values: {consensus_metrics['feature_presence']['missing_values_pct']:.1f}% of intensity matrix\n"
            text += f"Features present in all samples: {consensus_metrics['feature_presence']['complete']} ({complete_pct:.1f}%)\n"
        else:
            text += "\nConsensus map: No consensus data available\n"
        
        # Add QC metrics if available
        if qc_metrics:
            text += "\nQC metrics:\n"
            text += f"  Mean RSD: {qc_metrics['rsd_mean']:.2f}%\n"
            text += f"  Median RSD: {qc_metrics['rsd_median']:.2f}%\n"
            text += f"  Features with RSD < 20%: {qc_metrics['features_below_20rsd_pct']:.1f}%\n"
            text += f"  Features with RSD < 30%: {qc_metrics['features_below_30rsd_pct']:.1f}%\n"
        
        # Add text to the page
        plt.text(0.1, 0.85, text, fontsize=12, va='top', linespacing=1.5)
        pdf.savefig()
        plt.close()
        
        # Add all plots (one per page)
        for plot_path in plots:
            if plot_path and os.path.exists(plot_path):
                # Read the image
                img = plt.imread(plot_path)
                # Create a new figure
                plt.figure(figsize=(12, 8))
                # Display the image
                plt.imshow(img)
                plt.axis('off')
                # Save to PDF
                pdf.savefig()
                plt.close()
    
    return output_path


def save_qc_metadata(qc_data, output_path):
    """
    Save QC metadata to a JSON file for later integration with other systems.
    
    Parameters
    ----------
    qc_data : dict
        Dictionary containing QC results
    output_path : str
        Path to save the output JSON file
        
    Returns
    -------
    str
        Path to the saved JSON file
    """
    # Create a serializable document without raw data arrays
    # Make a clean copy to avoid modifying the original
    doc = {
        "run_id": qc_data.get("run_id", f"qc_{int(time.time())}"),
        "timestamp": time.time(),
        "date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "sample_count": len(qc_data.get("feature_metrics", [])),
        "feature_counts": [m.get("feature_count") for m in qc_data.get("feature_metrics", [])],
        "sample_names": [m.get("file_name") for m in qc_data.get("feature_metrics", [])],
        "report_path": qc_data.get("report_path"),
        "plots": qc_data.get("plots", {}),
    }
    
    # Add consensus metrics if available
    if qc_data.get("consensus_metrics"):
        doc["consensus_feature_count"] = qc_data["consensus_metrics"].get("feature_count")
        doc["missing_values_pct"] = qc_data["consensus_metrics"].get("feature_presence", {}).get("missing_values_pct")
    
    # Add QC metrics if available
    if qc_data.get("qc_metrics"):
        # Only include serializable parts of QC metrics
        doc["qc_metrics"] = {
            k: v for k, v in qc_data["qc_metrics"].items() 
            if not isinstance(v, (np.ndarray, list)) or k.startswith('_')
        }
    # Make sure any numpy types are converted to Python types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(i) for i in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        else:
            return obj
    
    doc = convert_numpy_types(doc)
    
    # Save to file
    with open(output_path, 'w') as f:
        json.dump(doc, f, indent=2)
    
    return output_path


def run_qc_advanced(mzml_files, feature_files, consensus_file=None, output_dir=None,
                  qc_name_pattern="QC", save_csv=True, save_pdf=True, save_json=True,
                  run_id=None, verbose=True):
    """
    Run comprehensive QC analysis on metabolomics data.
    
    Parameters
    ----------
    mzml_files : list
        List of paths to mzML files
    feature_files : list
        List of paths to featureXML files (same order as mzML)
    consensus_file : str, optional
        Path to consensusXML file (if available)
    output_dir : str, optional
        Directory to save results (default: current directory + "qc_results")
    qc_name_pattern : str, default="QC"
        Pattern to identify QC samples in filenames
    save_csv : bool, default=True
        Whether to save a CSV summary of QC metrics
    save_pdf : bool, default=True
        Whether to save a PDF report
    save_json : bool, default=True
        Whether to save metadata as JSON file
    run_id : str, optional
        Unique identifier for this QC run (default: timestamp-based)
    verbose : bool, default=True
        Whether to print progress messages
        
    Returns
    -------
    dict
        Dictionary containing results and file paths
    """
    assert len(mzml_files) == len(feature_files), "mzML and featureXML lists must have same length"
    
    # Set up output directory
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "qc_results")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate run ID if not provided
    if run_id is None:
        run_id = f"qc_{int(time.time())}"
    
    if verbose:
        print(f"Running QC analysis on {len(feature_files)} samples, output: {output_dir}")
    
    # Record start time for runtime calculation
    start_time = time.time()
    
    # Step 1: Load metrics from individual feature maps
    feature_metrics = []
    for fxml_path in feature_files:
        if verbose:
            print(f"Processing {fxml_path}")
        
        metrics = load_feature_map_metrics(fxml_path)
        feature_metrics.append(metrics)
    
    # Step 2: Load consensus map if available
    consensus_metrics = None
    intensity_matrix = None
    sample_names = [os.path.basename(m) for m in mzml_files]
    
    if consensus_file and os.path.exists(consensus_file):
        if verbose:
            print(f"Processing consensus map: {consensus_file}")
        
        consensus_metrics, cons_sample_names, intensity_matrix = load_consensus_map_metrics(consensus_file)
    
    # Step 3: Detect QC samples and calculate QC metrics
    qc_metrics = None
    rsd = None
    
    if consensus_metrics is not None:
        qc_indices = detect_qc_samples(consensus_metrics['samples'], qc_name_pattern)
        
        if qc_indices and len(qc_indices) >= 2:
            if verbose:
                print(f"Found {len(qc_indices)} QC samples, calculating metrics")
            
            qc_metrics, rsd = calculate_qc_metrics(intensity_matrix, qc_indices)
    
    # Step 4: Generate plots
    plots = {}
    
    # Feature intensity distributions
    plots['intensity_distribution'] = os.path.join(output_dir, "feature_intensity_distribution.png")
    plot_feature_intensity_distributions(feature_metrics, plots['intensity_distribution'])
    
    # RT and m/z distributions
    plots['rt_mz_distribution'] = os.path.join(output_dir, "rt_mz_distribution.png")
    plot_rt_mz_distribution(feature_metrics, plots['rt_mz_distribution'])
    
    if consensus_metrics is not None:
        # Intensity boxplot
        plots['intensity_boxplot'] = os.path.join(output_dir, "intensity_boxplot.png")
        plot_intensity_boxplot(intensity_matrix, consensus_metrics['samples'], plots['intensity_boxplot'])
        
        # RT-m/z scatter
        plots['rt_mz_scatter'] = os.path.join(output_dir, "rt_mz_scatter.png")
        plot_rt_mz_scatter(consensus_metrics, plots['rt_mz_scatter'])
    
    if qc_metrics is not None and rsd is not None:
        # RSD histogram
        plots['rsd_histogram'] = os.path.join(output_dir, "rsd_histogram.png")
        plot_rsd_histogram(rsd, plots['rsd_histogram'])
    
    # Step 5: Save summary CSV
    csv_path = None
    if save_csv:
        # Basic metrics per sample
        basic_metrics = []
        for metrics in feature_metrics:
            basic_metrics.append({
                'file_name': metrics['file_name'],
                'feature_count': metrics['feature_count'],
                'TIC': metrics['TIC'],
                'intensity_mean': metrics['intensity_mean'],
                'intensity_median': metrics['intensity_median'],
                'rt_min': metrics['rt_range'][0],
                'rt_max': metrics['rt_range'][1],
                'mz_min': metrics['mz_range'][0],
                'mz_max': metrics['mz_range'][1]
            })
        
        basic_df = pd.DataFrame(basic_metrics)
        csv_path = os.path.join(output_dir, "qc_summary.csv")
        basic_df.to_csv(csv_path, index=False)
        
        if verbose:
            print(f"Saved QC summary to {csv_path}")
    
    # Step 6: Generate PDF report
    report_path = None
    if save_pdf:
        report_path = os.path.join(output_dir, "qc_report.pdf")
        generate_qc_report(
            feature_metrics, 
            consensus_metrics or {'feature_count': 0, 'sample_count': 0, 'feature_presence': {'missing_values_pct': 0, 'complete': 0}}, 
            qc_metrics, 
            list(plots.values()), 
            report_path
        )
        
        if verbose:
            print(f"Saved QC report to {report_path}")
    
    # Step 7: Save metadata to JSON
    json_path = None
    if save_json:
        json_path = os.path.join(output_dir, "qc_metadata.json")
        qc_data = {
            "run_id": run_id,
            "feature_metrics": feature_metrics,
            "consensus_metrics": consensus_metrics,
            "qc_metrics": qc_metrics,
            "plots": plots,
            "csv_path": csv_path,
            "report_path": report_path
        }
        json_path = save_qc_metadata(qc_data, json_path)
        
        if verbose:
            print(f"Saved QC metadata to {json_path}")
    
    # Return results
    result = {
        "run_id": run_id,
        "runtime_sec": round(time.time() - start_time, 2),
        "csv_path": csv_path,
        "report_path": report_path,
        "json_path": json_path,
        "plots": plots,
        "qc_metrics": qc_metrics
    }
    
    return result


if __name__ == "__main__":
    # Example usage when script is run directly
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python quality_control.py <mzml_file1,mzml_file2,...> <feature_file1,feature_file2,...> [consensus_file]")
        sys.exit(1)
    
    mzml_files = sys.argv[1].split(',')
    feature_files = sys.argv[2].split(',')
    consensus_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = run_qc_advanced(mzml_files, feature_files, consensus_file)
    print(f"QC analysis complete. Report saved to: {result['report_path']}")
