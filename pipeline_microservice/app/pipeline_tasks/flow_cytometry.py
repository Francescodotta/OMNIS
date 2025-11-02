import redis.exceptions
from app import celery_microservice
from ..flow_cytometry_functions import fcs_utilities as fcs
import redis

@celery_microservice.task(name='app.pipeline_tasks.flow_cytometry.select_fcs_files')
def select_fcs_files_task(file_paths: list):
    """
    Celery task to read and process FCS files
    
    Args:
        file_paths (list): List of paths to FCS files
        
    Returns:
        list: List of serialized FCS data
    """
    try:
        # Read and serialize the FCS files
        serialized_data = fcs.read_batch_fcs_files(file_paths)
        return serialized_data
        
    except Exception as e:
        print(f"Error in read_fcs_files_task: {str(e)}")
        raise e
    
@celery_microservice.task(name='app.pipeline_tasks.flow_cytometry.umap_dimensionality_reduction')
def umap_dimensionality_reduction_task(json_str: str, data2) -> dict:
    try:
        result = fcs.umap_dimensionality_reduction(json_str, data2)
        print("UMAP dimensionality reduction task completed successfully")
        return result
    except Exception as e:
        print(f"Error in umap_dimensionality_reduction_task: {str(e)}")
        raise e



@celery_microservice.task(name='app.pipeline_tasks.flow_cytometry.louvain_clustering')
def louvain_clustering_task(json_str: str, k_neighbors: int = 100, resolution: float = 0.5) -> str:
    """
    Performs Louvain clustering on UMAP results
    
    Args:
        json_str (str): JSON string containing UMAP results
        k_neighbors (int): Number of nearest neighbors (default=100)
        resolution (float): Resolution parameter for clustering (default=0.5)
        
    Returns:
        str: JSON string containing clustering results
    """
    try:
        return fcs.louvain_clustering(json_str, k_neighbors, resolution)
    except Exception as e:
        print(f"Error in louvain_clustering_task: {str(e)}")
        raise e
    
@celery_microservice.task(bind = True, name='app.pipeline_tasks.flow_cytometry.leiden_clustering')
def leiden_clustering_task(self, data_paths: dict, resolution: float = 1.0) -> dict:
    try:
        result = fcs.leiden_clustering(self, data_paths, resolution)
        print("Leiden clustering task completed successfully")
        return result
    except Exception as e:
        print(f"Error in leiden_clustering_task: {str(e)}")
        raise e
    
    
@celery_microservice.task(bind=True, name='app.pipeline_tasks.flow_cytometry.generate_heatmap_data')
def generate_heatmap_data_task(self, data_paths: dict, other = 1) -> dict:
    try:
        print("Arguments received by generate_heatmap_data_task:")
        print("self:", self)
        print("data_paths:", data_paths)
        
        result = fcs.generate_heatmap_data(self, data_paths)
        print("Heatmap data generation task completed successfully")
        return result
    except Exception as e:
        print(f"Error in generating the heatmap data: {str(e)}")
        raise e
    

@celery_microservice.task(bind=True, name='app.pipeline_tasks.flow_cytometry.flowsom_clustering')
def flowsom_clustering_task(self, json_str: str, n_clusters: int, xdim: int, ydim: int) -> dict:
    try:
        result = fcs.flowsom_batch_pipeline(json_str, n_clusters, xdim, ydim)
        print("FlowSOM clustering task completed successfully")
        return result
    except Exception as e:
        print(f"Error in flowsom_clustering_task: {str(e)}")
        raise e

    
@celery_microservice.task(name='app.pipeline_tasks.flow_cytometry.plot_matrix')
def plot_matrix_task(data_paths: dict, data2=0) -> str:
    try:
        matrixplot_path = fcs.plot_matrix(data_paths, data2)
        print("Matrix plot task completed successfully")
        return matrixplot_path
    except Exception as e:
        print(f"Error in plot_matrix_task: {str(e)}")
        raise e

@celery_microservice.task(name='app.pipeline_tasks.flow_cytometry.plot_scatter')
def plot_scatter_task(data_paths: dict,data2 = 0) -> str:
    try:
        scatterplot_path = fcs.plot_scatter(data_paths, data2)
        print("Scatter plot task completed successfully")
        return scatterplot_path
    except Exception as e:
        print(f"Error in plot_scatter_task: {str(e)}")
        raise e