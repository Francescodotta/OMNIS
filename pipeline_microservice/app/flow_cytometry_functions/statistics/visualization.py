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


def heatmap_differences_visualization(pairwise_diff_df: pd.DataFrame, out_dir: str = "") -> str:
    """
    Generates a heatmap of pairwise differences (Treatment - Control).
    Expects a DataFrame where index is Sample Pairs and columns are Parameters.
    """
    # Ensure data is numeric
    plot_df = pairwise_diff_df.select_dtypes(include=[np.number])
    print(plot_df.head())
    
    if plot_df.empty:
        print("Warning: No numeric data to plot in heatmap.")
        return None

    # Plot setup
    fig, ax = plt.subplots(1, 1, figsize=(25, 8))
    
    # Generate Heatmap
    sns.heatmap(plot_df, ax=ax, cmap='RdBu_r', center=0,
                cbar_kws={'label': 'Difference (Treatment - Control) [z-score]'}, 
                linewidths=0.5, annot=False)
    
    # Styling
    ax.set_title("Treatment vs Control Effect", fontsize=18)
    ax.set_xlabel("Parameters (Channels + Scatter)", fontsize=18)
    ax.set_ylabel("Samples", fontsize=18)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.tight_layout()
    
    # Save
    out_path = os.path.join(out_dir, "microplastics_differences_heatmap.png")
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig) # Close plot to free memory
    
    print(f"Heatmap saved to {out_path}")
    return out_path


# ...existing code...

def heatmap_consistent_parameters(pairwise_diff_df: pd.DataFrame, out_dir: str = "") -> List[str]:
    """
    Generates heatmaps for parameters that are 100% consistently UP or DOWN regulated across all samples.
    
    Args:
        pairwise_diff_df: DataFrame with pairwise differences (index=Samples, columns=Parameters)
        out_dir: Output directory for saving figures
        
    Returns:
        List of paths to saved figures
    """
    saved_paths = []
    
    # Ensure data is numeric
    plot_df = pairwise_diff_df.select_dtypes(include=[np.number])
    if plot_df.empty:
        print("Warning: No numeric data to plot.")
        return []

    n_samples = len(plot_df)
    consistency_analysis = []

    # Analyze consistency for each parameter
    for param in plot_df.columns:
        param_values = plot_df[param].dropna()
        n_valid = len(param_values)
        
        if n_valid > 0:
            n_positive = (param_values > 0).sum()
            n_negative = (param_values < 0).sum()
            mean_val = param_values.mean()
            
            # Determine if 100% consistent
            is_100_up = (n_positive == n_valid) and (n_negative == 0)
            is_100_down = (n_negative == n_valid) and (n_positive == 0)
            
            consistency_analysis.append({
                'parameter': param,
                'mean_diff': mean_val,
                'is_100_up': is_100_up,
                'is_100_down': is_100_down
            })

    consistency_df = pd.DataFrame(consistency_analysis)
    
    # Filter 100% consistent parameters
    params_100_up = consistency_df[consistency_df['is_100_up']].sort_values('mean_diff', ascending=False)
    params_100_down = consistency_df[consistency_df['is_100_down']].sort_values('mean_diff', ascending=True)

    print(f"Parameters 100% UP-regulated: {len(params_100_up)}")
    print(f"Parameters 100% DOWN-regulated: {len(params_100_down)}")

    # --- HEATMAP 100% UP-REGULATED ---
    if len(params_100_up) > 0:
        n_up = min(30, len(params_100_up))
        top_up = params_100_up.head(n_up)
        up_diff = plot_df[top_up['parameter'].values]
        
        # Scale from 0 to max (all positive)
        vmax = np.nanmax(up_diff.values)
        
        fig, ax = plt.subplots(1, 1, figsize=(max(12, n_up*0.4), 6))
        sns.heatmap(up_diff, ax=ax, cmap='Reds', vmin=0, vmax=vmax,
                    cbar_kws={'label': 'Difference (Treatment - Control) [z-score]'}, 
                    linewidths=0.5, annot=False)
        
        ax.set_title(f"Consistently UP-regulated Parameters (n={n_up})\n"
                     f"All {n_samples} sample pairs show INCREASE", 
                     fontsize=15, fontweight='bold', color='darkred')
        ax.set_xlabel("Parameters", fontsize=14)
        ax.set_ylabel("Sample Pairs", fontsize=14)
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.tight_layout()
        
        out_path = os.path.join(out_dir, "heatmap_100pct_UP_regulated.png")
        fig.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(out_path)
        print(f"Saved UP-regulated heatmap to {out_path}")

    # --- HEATMAP 100% DOWN-REGULATED ---
    if len(params_100_down) > 0:
        n_down = min(30, len(params_100_down))
        top_down = params_100_down.head(n_down)
        down_diff = plot_df[top_down['parameter'].values]
        
        # Scale from min to 0 (all negative)
        vmin = np.nanmin(down_diff.values)
        
        fig, ax = plt.subplots(1, 1, figsize=(max(12, n_down*0.4), 6))
        sns.heatmap(down_diff, ax=ax, cmap='Blues_r', vmin=vmin, vmax=0,
                    cbar_kws={'label': 'Difference (Treatment - Control) [z-score]'}, 
                    linewidths=0.5, annot=False)
        
        ax.set_title(f"Consistently DOWN-regulated Parameters (n={n_down})\n"
                     f"All {n_samples} sample pairs show DECREASE", 
                     fontsize=15, fontweight='bold', color='darkblue')
        ax.set_xlabel("Parameters", fontsize=14)
        ax.set_ylabel("Sample Pairs", fontsize=14)
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.tight_layout()
        
        out_path = os.path.join(out_dir, "heatmap_100pct_DOWN_regulated.png")
        fig.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(out_path)
        print(f"Saved DOWN-regulated heatmap to {out_path}")
        
    # Save consistency analysis CSV
    csv_path = os.path.join(out_dir, "consistency_analysis.csv")
    consistency_df.to_csv(csv_path, index=False)
    
    return saved_paths



# bar plot for the cohen effect of each marker
def barplot_cohen_effect_size(cohen_df: pd.DataFrame, out_dir: str = "", top_n: int = 20) -> str:
    """
    Generates a bar plot of Cohen's d effect sizes for each marker with confidence intervals.
    
    Args:
        cohen_df: DataFrame with columns ['marker', 'cohen_d', 'ci_lower', 'ci_upper', 'direction', 'significant_fdr']
        out_dir: Output directory for saving figure
        top_n: Number of top markers to display (default: 20)
    Returns:
        Path to saved figure
    """
    
    # order markers by absolute cohen d
    cohen_df = cohen_df.reindex(cohen_df['cohen_d'].abs().sort_values(ascending=False).index)
    
    # TAKE TOP N MARKERS
    top_markers = cohen_df.head(top_n)
    
    if len(top_markers) == 0:
        print("Warning: No markers to plot.")
        return None
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    x_pos = np.arange(len(top_markers))
    
    # Color by direction (if available)
    if 'direction' in top_markers.columns:
        colors = ['#d73027' if d == 'UP' else '#4575b4' for d in top_markers['direction']]
    else:
        colors = ['#d73027' if d > 0 else '#4575b4' for d in top_markers['cohen_d']]
    
    bars = ax.bar(x_pos, top_markers['cohen_d'].values, 
                   color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    
    # Add CI as error bars (if available)
    if 'ci_lower' in top_markers.columns and 'ci_upper' in top_markers.columns:
        # Calculate error bars ensuring non-negative values
        yerr_lower = np.abs(top_markers['cohen_d'].values - top_markers['ci_lower'].values)
        yerr_upper = np.abs(top_markers['ci_upper'].values - top_markers['cohen_d'].values)
        
        ax.errorbar(x_pos, top_markers['cohen_d'].values,
                    yerr=[yerr_lower, yerr_upper],
                    fmt='none', ecolor='black', capsize=3, capthick=1.5, alpha=0.6)
        
        # Mark significant bars
        if 'significant_fdr' in top_markers.columns:
            for i, (idx, row) in enumerate(top_markers.iterrows()):
                if row['significant_fdr']:
                    # Calculate y position for significance marker
                    if row['cohen_d'] >= 0:
                        y_pos = row['ci_upper'] + np.abs(row['ci_upper'] - row['cohen_d']) * 0.15
                    else:
                        y_pos = row['ci_lower'] - np.abs(row['cohen_d'] - row['ci_lower']) * 0.15
                    ax.text(i, y_pos, '***', ha='center', va='bottom' if row['cohen_d'] >= 0 else 'top', 
                           fontsize=12, fontweight='bold')
    
    ax.axhline(0, color='black', linewidth=0.8, linestyle='-')
    ax.set_title(f"Top {len(top_markers)} Markers - Cohen's d Effect Size\nwith 95% CI and FDR significance", fontsize=18)
    ax.set_xlabel("Markers", fontsize=18)
    ax.set_ylabel("Cohen's d Effect Size", fontsize=18)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(top_markers['marker'].values, rotation=45, ha='right', fontsize=15)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#d73027', alpha=0.7, label='Positive Effect'),
        Patch(facecolor='#4575b4', alpha=0.7, label='Negative Effect')
    ]
    if 'significant_fdr' in top_markers.columns:
        legend_elements.append(Patch(facecolor='white', edgecolor='black', label='*** FDR < 0.05'))
    ax.legend(handles=legend_elements, loc='best')
    
    plt.tight_layout()
    
    out_path = os.path.join(out_dir, "cohen_effect_size_barplot.png")
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Cohen's d bar plot saved to {out_path}")
    return out_path


def barplot_cohen_effect_size_horizontal(cohen_df: pd.DataFrame, out_dir: str = "", top_n: int = 20) -> str:
    """
    Generates a horizontal bar plot of Cohen's d effect sizes with confidence intervals and effect size thresholds.
    
    Args:
        cohen_df: DataFrame with columns ['marker', 'cohen_d', 'ci_lower', 'ci_upper', 'direction', 'significant_fdr']
        out_dir: Output directory for saving figure
        top_n: Number of top markers to display (default: 20)
    Returns:
        Path to saved figure
    """
    
    # order markers by absolute cohen d
    cohen_df = cohen_df.reindex(cohen_df['cohen_d'].abs().sort_values(ascending=False).index)
    
    # TAKE TOP N MARKERS
    top_markers = cohen_df.head(top_n)
    
    if len(top_markers) == 0:
        print("Warning: No markers to plot.")
        return None
    
    fig, ax = plt.subplots(1, 1, figsize=(10, max(8, top_n * 0.4)))
    y_pos = np.arange(len(top_markers))
    
    # Color by direction (if available)
    if 'direction' in top_markers.columns:
        colors = ['#d73027' if d == 'UP' else '#4575b4' for d in top_markers['direction']]
    else:
        colors = ['#d73027' if d > 0 else '#4575b4' for d in top_markers['cohen_d']]
    
    bars = ax.barh(y_pos, top_markers['cohen_d'].values, 
                    color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    
    # Add CI as error bars (if available)
    if 'ci_lower' in top_markers.columns and 'ci_upper' in top_markers.columns:
        # Calculate error bars ensuring non-negative values
        xerr_lower = np.abs(top_markers['cohen_d'].values - top_markers['ci_lower'].values)
        xerr_upper = np.abs(top_markers['ci_upper'].values - top_markers['cohen_d'].values)
        
        ax.errorbar(top_markers['cohen_d'].values, y_pos,
                    xerr=[xerr_lower, xerr_upper],
                    fmt='none', ecolor='black', capsize=3, capthick=1.5, alpha=0.6)
        
        # Mark significant bars
        if 'significant_fdr' in top_markers.columns:
            for i, (idx, row) in enumerate(top_markers.iterrows()):
                if row['significant_fdr']:
                    # Calculate x position for significance marker
                    if row['cohen_d'] >= 0:
                        x_pos_sig = row['ci_upper'] + np.abs(row['ci_upper'] - row['cohen_d']) * 0.15
                    else:
                        x_pos_sig = row['ci_lower'] - np.abs(row['cohen_d'] - row['ci_lower']) * 0.15
                    ax.text(x_pos_sig, i, '***', ha='left' if row['cohen_d'] >= 0 else 'right', 
                           va='center', fontsize=12, fontweight='bold')
    
    # Add vertical line at zero
    ax.axvline(0, color='black', linewidth=0.8)
    
    # Effect size thresholds (Cohen: small=0.2, medium=0.5, large=0.8)
    for thresh, label in [(0.2, 'small'), (0.5, 'medium'), (0.8, 'large')]:
        ax.axvline(thresh, color='gray', linestyle='--', alpha=0.4)
        ax.axvline(-thresh, color='gray', linestyle='--', alpha=0.4)
    
    ax.set_title(f"Top {len(top_markers)} Parameters by Effect Size (Cohen's d)\n(*** FDR < 0.05)", 
                 fontsize=12)
    ax.set_xlabel("Cohen's d (Effect Size)", fontsize=11)
    ax.set_ylabel("Parameters", fontsize=11)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_markers['marker'].values)
    ax.invert_yaxis()
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#d73027', alpha=0.7, label='Positive Effect'),
        Patch(facecolor='#4575b4', alpha=0.7, label='Negative Effect')
    ]
    if 'significant_fdr' in top_markers.columns:
        legend_elements.append(Patch(facecolor='white', edgecolor='black', label='*** FDR < 0.05'))
    ax.legend(handles=legend_elements, loc='best')
    
    plt.tight_layout()
    
    out_path = os.path.join(out_dir, "cohen_effect_size_horizontal_barplot.png")
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Cohen's d horizontal bar plot saved to {out_path}")
    return out_path


def volcano_plot_exploratory(stats_df: pd.DataFrame, out_dir: str = "", p_threshold: float = 0.01, 
                             top_n_labels: int = 10) -> str:
    """
    Generates a volcano plot showing mean differences vs -log10(p-value) for exploratory analysis.
    Uses uncorrected p-values (not adjusted for multiple testing).
    
    Args:
        stats_df: DataFrame with columns ['parameter', 'mean_difference', 'p_value', 'direction']
        out_dir: Output directory for saving figure
        p_threshold: P-value threshold for highlighting significant points (default: 0.01)
        top_n_labels: Number of top hits to label on the plot (default: 10)
        
    Returns:
        Path to saved figure
    """
    
    if stats_df.empty:
        print("Warning: No data to plot in volcano plot.")
        return None
    
    # Calculate -log10(p-value), handle p=0 cases
    stats_df = stats_df.copy()
    stats_df['-log10_pval'] = stats_df['p_value'].apply(
        lambda p: -np.log10(p) if p > 0 else -np.log10(1e-300)
    )
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Separate points by significance
    significant = stats_df[stats_df['p_value'] < p_threshold]
    not_significant = stats_df[stats_df['p_value'] >= p_threshold]
    
    # Plot non-significant points
    if len(not_significant) > 0:
        ax.scatter(not_significant['mean_difference'], 
                  not_significant['-log10_pval'],
                  c='gray', alpha=0.5, s=50, label='Not significant', edgecolors='none')
    
    # Plot significant points by direction
    if len(significant) > 0:
        sig_up = significant[significant['mean_difference'] > 0]
        sig_down = significant[significant['mean_difference'] < 0]
        
        if len(sig_up) > 0:
            ax.scatter(sig_up['mean_difference'], 
                      sig_up['-log10_pval'],
                      c='#d73027', alpha=0.7, s=80, label=f'UP (p < {p_threshold})', 
                      edgecolors='black', linewidths=0.5)
        
        if len(sig_down) > 0:
            ax.scatter(sig_down['mean_difference'], 
                      sig_down['-log10_pval'],
                      c='#4575b4', alpha=0.7, s=80, label=f'DOWN (p < {p_threshold})', 
                      edgecolors='black', linewidths=0.5)
    
    # Add threshold lines
    ax.axhline(-np.log10(p_threshold), color='black', linestyle='--', 
               linewidth=1, alpha=0.5, label=f'p = {p_threshold}')
    ax.axvline(0, color='black', linestyle='-', linewidth=0.8, alpha=0.3)
    
    # Label top hits
    top_hits = stats_df[stats_df['p_value'] < p_threshold].head(top_n_labels)
    for _, row in top_hits.iterrows():
        xi = row['mean_difference']
        yi = row['-log10_pval']
        ax.text(xi, yi + 0.05, row['marker'], fontsize=10, rotation=0, 
               alpha=0.8, ha='center', va='bottom')
    
    # Styling
    ax.set_xlabel('Mean Difference (z-score)', fontsize=15)
    ax.set_ylabel('-log10(p-value)', fontsize=15)
    ax.set_title('Volcano Plot: Exploratory Analysis (uncorrected p-values)\n⚠️ Not corrected for multiple testing', 
                 fontsize=15, fontweight='bold')
    ax.legend(loc='best', fontsize=12, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    
    plt.tight_layout()
    
    # Save
    out_path = os.path.join(out_dir, "volcano_plot_exploratory_uncorrected_pvalues.png")
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Volcano plot saved to {out_path}")
    return out_path