import flowkit as fk
import pandas as pd
import anndata as ad
import scanpy as sc
import os 


def umap_dimensionality_reduction(
    df_fcs: pd.DataFrame,
    n_neighbors: int = 100,
    min_dist: float = 0.1,
    n_components: int = 2,
    metric: str = 'euclidean',
    metadata_columns: list = []
) -> ad.AnnData:
    """
    Perform UMAP dimensionality reduction on flow cytometry data.
    Keeps progressive_id, filename, and sample_id aligned in adata.obs.
    """
    # Remove columns with NaN values
    nan_columns = df_fcs.columns[df_fcs.isna().any()].tolist()
    if nan_columns:
        print(f"Columns with NaN values: {nan_columns}")
    df_fcs = df_fcs.dropna(axis=1)

    # Convert metadata_columns (dict_keys) to a list if necessary
    metadata_columns = list(metadata_columns)

    # Add mandatory columns to exclude
    columns_to_exclude = metadata_columns + ['sample_id', 'filename', 'file_id']

    # Select only numeric columns for UMAP, excluding specified columns
    df_numeric = df_fcs.select_dtypes(include=['number']).drop(columns=columns_to_exclude, errors='ignore')

    # Remove rows with sum zero
    df_numeric = df_numeric[df_numeric.sum(axis=1) != 0]
    # Remove rows with NaN
    df_numeric = df_numeric.dropna(axis=0)
    
    marker_names = df_numeric.columns.tolist()

    # Filter metadata columns to match df_numeric index
    obs = pd.DataFrame(index=df_numeric.index)

    # Add mandatory columns: sample_id, file_id, filename
    mandatory_columns = ["sample_id", "file_id", "filename"]
    for col in mandatory_columns:
        if col in df_fcs.columns:
            obs[col] = df_fcs.loc[df_numeric.index, col].values
        else:
            raise ValueError(f"Mandatory column '{col}' not found in the data.")

    # Add metadata columns
    for col in metadata_columns:
        if col in df_fcs.columns:
            obs[col] = df_fcs.loc[df_numeric.index, col].values
        else:
            raise ValueError(f"Metadata column '{col}' not found in the data.")

    print("Metadata columns added to obs:", obs.columns.tolist())

    # Create AnnData object
    adata = ad.AnnData(X=df_numeric.values, obs=obs)
    # Add the name of the columns
    adata.var_names = marker_names
    # Check for NaN in adata
    if adata.X is None or pd.isnull(adata.X).any():
        raise ValueError("AnnData object contains NaN values.")

    # Perform UMAP
    sc.pp.scale(adata)
    sc.tl.pca(adata, svd_solver='arpack')
    sc.pp.neighbors(adata, n_neighbors=n_neighbors)
    sc.tl.umap(adata, min_dist=min_dist, n_components=n_components)

    return adata

def clustering(adata: ad.AnnData, method: str = 'louvain', **kwargs) -> ad.AnnData:
    """
    Perform clustering on UMAP results using specified method.
    
    Args:
        adata (ad.AnnData): AnnData object containing UMAP results.
        method (str): Clustering method ('louvain' or 'leiden').
        **kwargs: Additional parameters for clustering methods.
        
    Returns:
        ad.AnnData: AnnData object with clustering results in .obs['clusters'].
    """
    if method == 'louvain':
        sc.tl.louvain(adata, **kwargs)
        adata.obs['clusters'] = adata.obs['louvain']
    elif method == 'leiden':
        sc.tl.leiden(adata, **kwargs)
        adata.obs['clusters'] = adata.obs['leiden']
    else:
        raise ValueError("Unsupported clustering method. Use 'louvain' or 'leiden'.")
    
    return adata

def flowsom_clustering(adata: ad.AnnData, n_clusters: int = 10, xdim: int = 10, ydim: int = 10) -> ad.AnnData:
    """
    Perform FlowSOM clustering on UMAP results.
    
    Args:
        adata (ad.AnnData): AnnData object containing UMAP results.
        n_clusters (int): Number of clusters for FlowSOM (default=10).
        xdim (int): X dimension of the SOM grid (default=10).
        ydim (int): Y dimension of the SOM grid (default=10).
        
    Returns:
        ad.AnnData: AnnData object with FlowSOM clustering results in .obs['flowsom_clusters'].
    """
    import flowsom as fs
    
    # Create FlowSOM object
    som = fs.FlowSOM(adata.X, xdim=xdim, ydim=ydim)
    
    # Train the SOM
    som.train()
    
    # Perform meta-clustering
    meta_clusters = som.meta_clustering(n_clusters=n_clusters)
    
    # Assign clusters to AnnData
    adata.obs['flowsom_clusters'] = meta_clusters
    
    return adata

def plot_umap_leiden_clusters(adata: ad.AnnData, title: str = 'UMAP with Leiden Clusters') -> str:
    """
    Plot UMAP results colored by Leiden clusters.
    
    Args:
        adata (ad.AnnData): AnnData object containing UMAP results and clustering.
        title (str): Title of the plot.
    """
    import matplotlib.pyplot as plt
    
    sc.pl.umap(adata, color='clusters', title=title, show=True)
    plt.savefig('umap_leiden_clusters.png')
    return 'umap_leiden_clusters.png'
    
def plot_umap_flowsom_clusters(adata: ad.AnnData, title: str = 'UMAP with FlowSOM Clusters') -> str:
    """
    Plot UMAP results colored by FlowSOM clusters.
    
    Args:
        adata (ad.AnnData): AnnData object containing UMAP results and FlowSOM clustering.
        title (str): Title of the plot.
    """
    import matplotlib.pyplot as plt
    
    sc.pl.umap(adata, color='flowsom_clusters', title=title, show=True)
    # save the figure
    plt.savefig('umap_flowsom_clusters.png')
    return 'umap_flowsom_clusters.png'
    
def plot_umap_sample_ids(adata: ad.AnnData, title: str = 'UMAP with Sample IDs') -> str:
    """
    Plot UMAP results colored by sample IDs.
    
    Args:
        adata (ad.AnnData): AnnData object containing UMAP results and sample IDs.
        title (str): Title of the plot.
    """
    import matplotlib.pyplot as plt
    
    sc.pl.umap(adata, color='sample_id', title=title, show=True)
    plt.savefig('umap_sample_ids.png')
    return 'umap_sample_ids.png'
    
# generate a plot for each marker expression on the UMAP
def plot_umap_marker_expression(adata: ad.AnnData) -> str:
    """
    Plot UMAP results colored by expression of a specific marker.
    
    Args:
        adata (ad.AnnData): AnnData object containing UMAP results and marker expressions.
        marker (str): Marker name to plot.
    """
    import matplotlib.pyplot as plt
    # make dir if not exists
    out_dir = 'umap_marker_plots'
    os.makedirs(out_dir, exist_ok=True)
    
    for marker in adata.var_names:
        if marker not in adata.var_names:
            raise ValueError(f"Marker '{marker}' not found in the data.")
        
        sc.pl.umap(adata, color=marker, title=f'UMAP with {marker} Expression', show=True)
        plt.savefig(f'{out_dir}/umap_{marker}_expression.png')
    return f'{out_dir}'





