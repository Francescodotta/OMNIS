import flowkit as fk
import pandas as pd
import umap
from typing import List, Dict
import flowsom as fs 
import anndata as ad
import phenograph
from sklearn.preprocessing import StandardScaler
import numpy as np
import scanpy as sc
import matplotlib.pyplot as plt
import uuid
from dotenv import load_dotenv
import os
from app.models import flow_cytometry
import logging


# set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define the path to the FCS files  
FLOW_CYTOMETRY_SAVE_PATH = os.getenv("FLOW_CYTOMETRY_SAVE_PATH")


def serialize_fcs_data(df: pd.DataFrame) -> str:
    """
    Serializes a Flow Cytometry DataFrame to JSON string
    
    Args:
        df (pd.DataFrame): Flow cytometry data DataFrame
        
    Returns:
        str: JSON string of the DataFrame
    """
    try:
        # Reset index and convert to JSON string
        df = df.reset_index(drop=True)
        json_str = df.to_json(orient='split', date_format='iso')
        
        logger.info("Serialized FCS data") # Insert the Chain ID
        
        return json_str
    
    except Exception as e:
        logger.error(f"Error serializing FCS data: {str(e)}") # insert the Chain ID
        print(f"Error serializing FCS data: {str(e)}")
        raise

def deserialize_fcs_data(json_str: str) -> pd.DataFrame:
    """
    Deserializes JSON string back into a DataFrame
    
    Args:
        json_str (str): JSON string containing DataFrame data
        
    Returns:
        pd.DataFrame: Reconstructed Flow Cytometry DataFrame
    """
    try:        
        if not isinstance(json_str, str):
            logger.error(f"Expected string input, got {type(json_str)}") # insert the Chain ID
            raise TypeError(f"Expected string input, got {type(json_str)}")
        
        logger.info("Deserializing FCS data") # insert the Chain ID
        
        return pd.read_json(json_str)
    
    except Exception as e:
        
        logger.error(f"Error deserializing FCS data: {str(e)}") # insert the Chain ID
        
        print(f"Error deserializing FCS data: {str(e)}")
        raise


def read_batch_fcs_files(file_paths: List[str]) -> str:
    """
    Reads multiple FCS files, concatenates their DataFrames, and returns a serialized JSON string.
    
    Args:
        file_paths (list): List of paths to FCS files
        
    Returns:
        str: Serialized JSON string of the concatenated DataFrame
    """
    try:
        # Load all samples using FlowKit
        samples = fk.load_samples(file_paths)
        
        # Process each sample and concatenate the raw data into a single DataFrame
        dataframes = []
        for sample in samples:
            # Convert to DataFrame without multi-index
            df = sample.as_dataframe(source='raw', col_multi_index=False)
            print("DataFrame shape:", df.shape, "\n", "DataFrame columns:", df.columns)
            
            # add the source file
            df['source_file'] = sample
            
            # remove NaN values
            df = df.dropna()
            dataframes.append(df)
            del df
        
        # Concatenate all DataFrames into a single DataFrame
        print("\n\n creating the concatenated df\n\n")
        concatenated_df = pd.concat(dataframes, ignore_index=True)
        del dataframes
        del samples
        
        # Serialize the concatenated DataFrame to JSON
        print("\n\n\n concatenating the df into a json object \n\n")
        unique_id = str(uuid.uuid4())
        json_str = os.path.join(FLOW_CYTOMETRY_SAVE_PATH, f"concatenated_df_{unique_id}.csv")
        concatenated_df.to_csv(json_str, index=False)
        
        del concatenated_df
        
        logger.info("Read batch FCS files") # insert the Chain ID
        
        print("Batch files read correctly\n\n\n")
        
        return json_str
    except Exception as e:
        logger.error(f"Error reading batch FCS files: {str(e)}") # insert the Chain ID
        print(f"Error processing FCS files: {str(e)}")
        raise

def umap_dimensionality_reduction(json_str: str, data2="") -> dict:
    try:
        n_components = 2
        print("\n starting dimensionality reduction analysis\n\n")
        df = pd.read_csv(json_str)
        
        df.fillna(0, inplace=True)

        # Store the source_file column separately
        source_files = None
        if 'source_file' in df.columns:
            source_files = df['source_file']
            df = df.drop('source_file', axis=1)

        # Perform UMAP dimensionality reduction
        reducer = umap.UMAP(n_components=n_components)
        reduced_data = reducer.fit_transform(df)

        # Create DataFrames
        reduced_df = pd.DataFrame(
            reduced_data,
            columns=[f'UMAP_{i+1}' for i in range(n_components)]
        )
        
        del reduced_data

        # Add source_file back to the DataFrames if it existed
        if source_files is not None:
            reduced_df['source_file'] = source_files
            df['source_file'] = source_files

        full_df = pd.concat([df.reset_index(drop=True), reduced_df], axis=1)

        # Generate unique filenames
        unique_id = str(uuid.uuid4())
        reduced_data_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, f"reduced_data_{unique_id}.csv"
        )
        original_data_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, f"original_data_{unique_id}.csv"
        )
        full_data_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, f"full_data_{unique_id}.csv"
        )

        # Save DataFrames to CSV files
        reduced_df.to_csv(reduced_data_path, index=False)
        df.to_csv(original_data_path, index=False)
        full_df.to_csv(full_data_path, index=False)

        logger.info("Performed UMAP dimensionality reduction")

        # Free up memory by deleting DataFrames
        del df
        del reduced_df
        del full_df

        return {
            "reduced_data_path": reduced_data_path,
            "original_data_path": original_data_path,
            "full_data_path": full_data_path
        }
    except Exception as e:
        logger.info(f"Error performing UMAP dimensionality reduction: {str(e)}")
        print(f"Error performing UMAP dimensionality reduction: {str(e)}")
        raise


def louvain_clustering(json_str: str, k_neighbors: int = 2, resolution: float = 0.1) -> str:
    try:
        # default values
        k_neighbors = 1000
        resolution = 0.2
        
        # Deserialize the JSON string to a DataFrame
        df = deserialize_fcs_data(json_str)
        
        # Store the source_file column separately
        source_files = None
        if 'source_file' in df.columns:
            source_files = df['source_file']
            df = df.drop('source_file', axis=1)
        
        # Scale the data
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(df)
        
        # Perform Louvain clustering
        communities, graph, Q = phenograph.cluster(
            data_scaled,
            clustering_algo='louvain',
            k=k_neighbors,
            resolution_parameter=resolution,
            seed=42,  # for reproducibility
        )
        
        # Create a DataFrame with the clustering results
        result_df = pd.DataFrame({
            'cluster': communities,
            'modularity': Q
        })
        
        # Add the original coordinates
        for col in df.columns:
            result_df[col] = df[col]
            
        # Add source_file back if it existed
        if source_files is not None:
            result_df['source_file'] = source_files
        
        # Serialize the results
        json_result = result_df.to_json(orient='split', date_format='iso')
        
        logger.info("Performed Louvain clustering")
        
        return json_result
    
    except Exception as e:
        logger.info(f"Error performing Louvain clustering: {str(e)}")
        print(f"Error performing Louvain clustering: {str(e)}")
        raise



def leiden_clustering(self, data_paths: dict, resolution: float = 1.0) -> dict:
    chain_id = self.request.id
    print(f"Chain ID: {chain_id}")
    try:
        resolution = 0.3
        
        print("Starting Leiden clustering with resolution:", resolution)

        # Load reduced data from file path
        reduced_df = pd.read_csv(data_paths['reduced_data_path'])
        full_df = pd.read_csv(data_paths['full_data_path'])

        # Store source_file information
        source_files = None
        if 'source_file' in reduced_df.columns:
            source_files = reduced_df['source_file']
            reduced_df = reduced_df.drop('source_file', axis=1)

        
        
        # Convert to AnnData for clustering
        adata = sc.AnnData(reduced_df.values)
        del reduced_df
        sc.pp.neighbors(adata, use_rep='X')
        sc.tl.leiden(adata, resolution=resolution)
        
        # Add clustering results to full_df
        full_df['Leiden_Cluster'] = adata.obs['leiden'].values

        # Add source_file back if it existed
        if source_files is not None:
            full_df['source_file'] = source_files

        # Save clustering results
        clustering_result_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, f"clustering_result_{uuid.uuid4()}.csv"
        )
        full_df.to_csv(clustering_result_path, index=False)
        
        del adata
        del full_df
        
        # update the pipeline run with the clustering results
        flow_cytometry.FlowCytoPipelineRun.update_by_chain_id(chain_id, {"clustering_result_path": clustering_result_path})
        
        logger.info("Performed Leiden clustering")
        
        # Return file paths
        return {
            "clustering_result_path": clustering_result_path,
            "full_data_path": data_paths['full_data_path'],
            "original_data_path": data_paths['original_data_path']
        }
    except Exception as e:
        logger.error(f"Error performing Leiden clustering: {str(e)}")
        print(f"Error performing Leiden clustering: {str(e)}")
        raise


# out of this leiden clustering generate a dataframe for heatmap based on Columns, and Leiden_Cluster
def generate_heatmap_data(self, data_paths: dict) -> dict:
    chain_id = self.request.id
    
    try:
        # Load clustering results
        clustering_df = pd.read_csv(data_paths['clustering_result_path'])
        
        # drop source file 
        clustering_df = clustering_df.drop(columns = "source_file")
        
        # Drop the UMAP columns
        clustering_df = clustering_df.drop(columns=['UMAP_1', 'UMAP_2'])
        
        # Store Leiden_Cluster separately as it's needed for grouping
        leiden_clusters = clustering_df['Leiden_Cluster']
        clustering_df = clustering_df.drop(columns=['Leiden_Cluster'])
        
        # Keep only numeric columns
        numeric_columns = clustering_df.select_dtypes(include=['int64', 'float64']).columns
        clustering_df = clustering_df[numeric_columns]
        
        # Normalize the data to range [0, 1]
        normalized_df = (clustering_df - clustering_df.min()) / (clustering_df.max() - clustering_df.min())
        del clustering_df
        
        # Add Leiden_Cluster back for grouping
        normalized_df['Leiden_Cluster'] = leiden_clusters
        
        # Generate heatmap data
        heatmap_data = normalized_df.groupby('Leiden_Cluster').mean()
        del normalized_df
        
        # Save heatmap data
        heatmap_data_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, f"heatmap_data_{uuid.uuid4()}.csv"
        )
        
        heatmap_data.to_csv(heatmap_data_path)
        
        del heatmap_data
        
        # Update the pipeline run with the heatmap data in the mongo db using the chain id
        flow_cytometry.FlowCytoPipelineRun.update_by_chain_id(chain_id, {
            "heatmap_data_path": heatmap_data_path, 
            "clustering_result_path": data_paths['clustering_result_path'], 
            "full_data_path": data_paths['full_data_path'], 
            "original_data_path": data_paths['original_data_path'],
            'status': 'completed'
        })
        
        logger.info("Generated heatmap data")
        
        return {
            "heatmap_data_path": heatmap_data_path,
            "clustering_result_path": data_paths['clustering_result_path'], 
            "full_data_path": data_paths['full_data_path'],
            "original_data_path": data_paths['original_data_path']
        }
    except Exception as e:
        logger.error(f"Error generating heatmap data: {str(e)}")
        print(f"Error generating heatmap data: {str(e)}")
        raise
    


def fcs_anndata_batch_from_json(json_str: str) -> ad.AnnData:
    """
    Convert a concatenated FCS DataFrame (from a JSON string containing its file path) 
    into an AnnData object with batch annotations.

    Parameters:
        json_str (str): JSON string containing the path to the concatenated FCS DataFrame.

    Returns:
        ad.AnnData: A single AnnData object containing all the data from the FCS files.
    """
    try:
        # Load the file path from the JSON string
        concatenated_df_path = json_str
        print(f"Loading concatenated DataFrame from: {concatenated_df_path}")

        # Read the concatenated DataFrame from the file
        concatenated_df = pd.read_csv(concatenated_df_path)

        # Store source_file information
        source_files = None
        if 'source_file' in concatenated_df.columns:
            source_files = concatenated_df['source_file']
            concatenated_df = concatenated_df.drop('source_file', axis=1)

        # Fill NaN values with 0
        concatenated_df.fillna(0, inplace=True)

        # Check for NaN values
        if concatenated_df.isnull().values.any():
            raise ValueError("NaN values found in the concatenated DataFrame.")

        # Handle multi-index columns if present
        if isinstance(concatenated_df.columns, pd.MultiIndex):
            concatenated_df.columns = concatenated_df.columns.get_level_values(0)

        # Remove all columns that contain "-W" or "-A"
        concatenated_df = concatenated_df.loc[:, ~concatenated_df.columns.str.contains('-W| -A')]

        # Convert all data to float64
        numeric_columns = concatenated_df.select_dtypes(include=['int64', 'float64']).columns
        concatenated_df = concatenated_df[numeric_columns].astype(np.float64)

        # Ensure index and columns dtype is object
        if concatenated_df.index.name is None:
            concatenated_df.index.name = 'cell_id'

        # Create AnnData object with C-contiguous array
        adata = ad.AnnData(
            X=np.ascontiguousarray(concatenated_df.values),
            obs=pd.DataFrame(index=concatenated_df.index),
            var=pd.DataFrame(index=concatenated_df.columns)
        )

        # Set variable names
        adata.var_names = concatenated_df.columns
        adata.obs_names = concatenated_df.index

        # Add batch information if available
        if source_files is not None:
            adata.obs['batch'] = source_files.astype(str)
        else:
            adata.obs['batch'] = 'unknown_batch'

        print("AnnData object created successfully.")
        return adata

    except Exception as e:
        print(f"Error processing concatenated FCS DataFrame: {str(e)}")
        raise



## run flowsom clustering on batch anndata and plot clusters with batch references 
def run_flowsom_clustering_batch_files(adata: ad.AnnData, n_clusters: int, xdim: int, ydim: int, cols_to_use: list):
    """
    Perform flowsom clustering on batch anndata object and plot clusters referencing original batch informations 
    
    Parameters:
        adata (ad.AnnData): Batch anndata object
        n_clusters (int): Number of clusters to use for flowsom clustering
        xdim (int): Number of x-dimension for flowsom clustering
        ydim (int): Number of y-dimension for flowsom clustering
        cols_to_use (list): List of columns to use for flowsom clustering
        
    Returns:
        Tuple[fs.FlowSOM, pd.DataFrame]: FlowSOM object and clustering results.
    """
    # Initialize FlowSOM
    fsom = fs.FlowSOM(
        inp=adata,
        n_clusters=n_clusters,
        xdim=xdim,
        ydim=ydim,
        cols_to_use=cols_to_use,
        seed=42
    )
    
    # Perform clustering
    ff_clustering = fs.flowsom_clustering(
        inp=adata,
        cols_to_use=cols_to_use,
        xdim=xdim,
        ydim=ydim,
        n_clusters=n_clusters,
        seed=42
    )
    
    # Check if ff_clustering is an AnnData object
    if isinstance(ff_clustering, ad.AnnData):
        # Print available keys to debug
        print("Available keys in ff_clustering.obs:", ff_clustering.obs.columns)
        # Try to get clustering from the first column
        cluster_column = ff_clustering.obs.columns[0]
        adata.obs['FlowSOM_cluster'] = ff_clustering.obs[cluster_column].astype(str)
    else:
        raise ValueError("Unexpected type for ff_clustering: {}".format(type(ff_clustering)))
    
    # Create UMAP embedding for visualization
    sc.pp.neighbors(adata, use_rep='X')
    sc.tl.umap(adata)
    
    # Plotting
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(50, 10))
    
    sc.pl.umap(adata, color='FlowSOM_cluster', ax=ax1, show=False, title='FlowSOM Clusters')
    sc.pl.umap(adata, color='batch', ax=ax2, show=False, title='Batch Reference')
    
    plt.tight_layout()
    plt.savefig('flowsom_clusters_batches.png', dpi=300)
    plt.close()
    
    return fsom, ff_clustering



## FLOWSOM PIPELINE
def flowsom_pipeline(fcs_file_path, n_clusters: int, xdim: int, ydim: int, cols_to_use: list) -> dict:
    """
    This function performs the following steps:
    1. Load the FCS file
    2. Convert the FCS file to an AnnData object
    3. Run FlowSOM clustering
    4. Return the FlowSOM object and the clustering results
    
    Args:
        fcs_file_path (str): The path to the FCS file
        n_clusters (int): The number of clusters to use
        xdim (int): The number of x-dimensions to use
        ydim (int): The number of y-dimensions to use
        cols_to_use (list): The columns to use for the clustering
        
    Returns:
        dict: A dictionary containing the FlowSOM object and the clustering results
    """
    
    
    fcs_sample = fk.Sample(fcs_file_path).as_dataframe(source="raw")
    
    # handle multi index columns 
    if isinstance(fcs_sample.columns, pd.MultiIndex):
        # Flatten the MultiIndex columns by taking the first level
        fcs_sample.columns = fcs_sample.columns.get_level_values(0)  # Get the first level

    # Step 3: Ensure index and columns dtype is object
    if fcs_sample.index.name is None:
        fcs_sample.index.name = 'cell_id'
    fcs_sample.index = fcs_sample.index.astype(str)
    fcs_sample.columns = fcs_sample.columns.astype(str)

    # Ensure variable names are unique
    assert fcs_sample.columns.is_unique, "Variable (marker) names must be unique."

    # Step 4: Create AnnData object
    adata = ad.AnnData(
        X=fcs_sample.values,
        obs=fcs_sample.index.to_frame(),
        var=pd.DataFrame(index=fcs_sample.columns)  # Variables annotations
    )

    # Assign variable and observation names
    adata.var_names = fcs_sample.columns.tolist()
    adata.obs_names = fcs_sample.index.tolist()
    logger.info(f"FCS file {fcs_file_path} converted to AnnData object") # insert the Chain ID
    
    
    fsom = fs.FlowSOM(
        inp = adata,
        n_clusters=n_clusters,
        xdim=xdim,
        ydim=ydim,
        cols_to_use=cols_to_use,
        seed = 42
    )
    
    # read the adata json object and transform it into an adata object
    adata = ad.read_h5ad(adata)
    
    # clustering 
    ff_clustering = fs.flowsom_clustering(inp = adata, cols_to_use=cols_to_use, xdim=xdim, ydim=ydim, n_clusters=n_clusters, seed=42)

    logger.info(f"FlowSOM clustering completed_1") # insert the Chain ID
    
    # return a json containing the fsom and ff_clustering
    result = {}
    result['fsom'] = fsom.to_json()
    result['ff_clustering'] = ff_clustering.to_json()
    return result



def flowsom_batch_pipeline(fcs_files_list, n_clusters: int, xdim: int, ydim: int):
    """
    Function to run the flowsom batch pipeline and save results to CSV.

    Args:
        fcs_files_list (_type_): List of fcs file paths
        n_clusters (int): Number of clusters you want to obtain out of flowsom
        xdim (int): dimension of x axis
        ydim (int): dimension of y axis

    Returns:
        dict: Dictionary containing paths to the saved CSV files and status message
    """
    try:
        # Create AnnData object
        adata = fcs_anndata_batch_from_json(fcs_files_list)
        markers = adata.var_names.to_list()
        
        # Run FlowSOM
        fsom, ff_clustering = run_flowsom_clustering_batch_files(
            adata, 
            n_clusters=n_clusters, 
            xdim=xdim, 
            ydim=ydim, 
            cols_to_use=markers
        )
        
        # Generate unique filenames
        unique_id = str(uuid.uuid4())
        clustering_result_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, 
            f"flowsom_clustering_{unique_id}.csv"
        )
        umap_result_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, 
            f"flowsom_umap_{unique_id}.csv"
        )
        
        # Create DataFrame with clustering results
        clustering_df = pd.DataFrame(
            adata.X,
            columns=adata.var_names,
            index=adata.obs_names
        )
        clustering_df['FlowSOM_cluster'] = adata.obs['FlowSOM_cluster']
        if 'batch' in adata.obs:
            clustering_df['batch'] = adata.obs['batch']
            
        # Add UMAP coordinates if they exist
        if 'X_umap' in adata.obsm:
            clustering_df['UMAP_1'] = adata.obsm['X_umap'][:, 0]
            clustering_df['UMAP_2'] = adata.obsm['X_umap'][:, 1]
        
        # Save results to CSV
        clustering_df.to_csv(clustering_result_path, index=True)
        
        return {
            "clustering_result_path": clustering_result_path,
        }
        
    except Exception as e:
        print(f"Error in flowsom_batch_pipeline: {str(e)}")
        raise


def plot_scatter(data_paths: dict, data2 = 0) -> str:
    try:
        # Load clustering results
        full_df = pd.read_csv(data_paths['full_data_path'])
        clustering_df = pd.read_csv(data_paths['clustering_result_path'])

        # Generate scatterplot
        plt.figure(figsize=(8, 8))
        scatter = plt.scatter(
            full_df['UMAP_1'],
            full_df['UMAP_2'],
            c=pd.to_numeric(clustering_df['Leiden_Cluster']),
            cmap='viridis',
            s=10
        )
        plt.colorbar(scatter, label='Leiden Cluster')
        plt.title("Scatterplot of Leiden Clusters")
        plt.xlabel('UMAP_1')
        plt.ylabel('UMAP_2')
        scatterplot_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, f"leiden_scatter_plot_{uuid.uuid4()}.png"
        )
        plt.savefig(scatterplot_path)
        plt.close()

        return scatterplot_path
    except Exception as e:
        print(f"Error plotting scatter plot: {str(e)}")
        raise
    
def plot_matrix(data_paths: dict, data2=0) -> str:
    try:
        # Load original data and clustering results
        original_df = pd.read_csv(data_paths['original_data_path'])
        clustering_df = pd.read_csv(data_paths['clustering_result_path'])

        # Ensure indices are aligned
        original_df.reset_index(drop=True, inplace=True)
        clustering_df.reset_index(drop=True, inplace=True)

        # Debugging: Print shapes and columns
        print(f"Original DataFrame shape: {original_df.shape}")
        print(f"Clustering DataFrame shape: {clustering_df.shape}")
        print(f"Original DataFrame columns: {list(original_df.columns)}")

        # Prepare data for plotting
        adata_full = sc.AnnData(original_df)

        # Set variable names
        adata_full.var_names = original_df.columns.astype(str)
        adata_full.var_names_make_unique()

        # Set observation names
        adata_full.obs_names = original_df.index.astype(str)

        # Assign clustering results to obs
        adata_full.obs['Leiden_Cluster'] = clustering_df['Leiden_Cluster'].astype('category').values

        # Debugging: Print AnnData structure
        print(f"AnnData shape: {adata_full.shape}")
        print(f"AnnData var_names: {adata_full.var_names}")
        print(f"AnnData obs_names: {adata_full.obs_names}")
        print(f"AnnData obs (first 5 rows):\n{adata_full.obs.head()}")

        # Generate matrix plot
        sc.pl.matrixplot(
            adata_full,
            groupby='Leiden_Cluster',
            var_names=list(adata_full.var_names),
            cmap="viridis",
            standard_scale="var",
            dendrogram=True,
            show=False
        )

        # Save the plot
        matrixplot_path = os.path.join(
            FLOW_CYTOMETRY_SAVE_PATH, f"leiden_matrix_plot_{uuid.uuid4()}.png"
        )
        plt.savefig(matrixplot_path, bbox_inches='tight')
        plt.close()

        return matrixplot_path

    except Exception as e:
        print(f"Error plotting matrix plot: {str(e)}")
        raise

