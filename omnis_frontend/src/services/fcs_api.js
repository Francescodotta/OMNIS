import api from '../utils/ApiFlowCytometry'


export const fetchPipelines = async (projectId) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/running_pipelines`);
        console.log('Fetched pipelines:', response.data);
        return response.data.data || [];
    } catch (error) {
        console.error('Error fetching pipelines:', error);
        throw new Error('Error fetching pipelines');
    }
}


export const fetchPipelinesDataClustering = async (projectId, pipelineId) => {
    try{
        const response = await api.get(`/api/v1/project/${projectId}/running_pipeline/${pipelineId}`);
        return response.data || [];
    }
    catch (error) {
        console.error('Error fetching pipeline data:', error);
        throw new Error('Error fetching pipeline data');
    }
}

// function to fetch the heatmap data
export const fetchHeatmap = async (projectId, pipelineId) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/heatmap/${pipelineId}`);
        return response.data || [];
    } catch (error) {
        console.error('Error fetching heatmap data:', error);
        throw new Error('Error fetching heatmap data');
    }
}



// function to fetch FCS file through progressive id for gating -- add the parentId as a query parameter
export const fetchGatingData = async (projectId, progressiveId, gatingStrategyId, parentId = null) => {
    try {
        console.log(progressiveId, projectId)
        // if parentId is not null, add it to the query parameter
        const queryParams = parentId ? `?parentId=${parentId}` : '';
        const response = await api.get(`/api/v1/project/${projectId}/flow_cytometry/${progressiveId}/gating_strategies/${gatingStrategyId}/scatterplot${queryParams}`);
        return response.data || [];
    } catch (error) {
        console.error('Error fetching gating data:', error);
        throw new Error('Error fetching gating data');
    }
}


// function to delete the gating strategy
export const deleteGatingStrategy = async (projectId, progressiveId, gatingStrategyId) => {
    try {
        const response = await api.delete(`/api/v1/project/${projectId}/flow_cytometry/${progressiveId}/gating_strategies/${gatingStrategyId}`);
        return response.data || [];
    }
    catch (error) {
        console.error('Error deleting gating strategy:', error);
        throw new Error('Error deleting gating strategy');
    }
}

// function to delete the pipeline
export const deletePipeline = async (projectId, pipelineId) => {
    try {
        const response = await api.delete(`/api/v1/project/${projectId}/pipeline/${pipelineId}`);
        console.log('Pipeline deleted:', response.data);
        return response.data;
    } catch (error) {
        console.error('Error deleting pipeline:', error);
        throw new Error('Error deleting pipeline');
    }
};
