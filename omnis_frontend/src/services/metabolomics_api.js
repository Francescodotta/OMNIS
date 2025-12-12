import api from '../utils/ApiMetabolomics';

export const fetchMetabolomicsPipelines = async (projectId) => {
    try{
        const response = await api.get(`/api/v1/project/${projectId}/pipelines`);
        console.log(response.data)
        return response.data || [];
    }catch(err){
        console.error('error fetching pipelines:', err);
        throw new Error('Error fetching pipelines for this project')
    }
}


export const deleteMetabolomicsPipeline = async(projectId, progressiveId) => {
    try{
        const response = await api.delete(`/api/v1/project/${projectId}/pipelines/${progressiveId}`);
        console.log('deletion of the pipeline')
        return response.data || [];
    }catch(e){
        console.error('Error deleting the pipeline', e);
        throw new Error('Error in deleting the pipeline')
    }
}


export const fetchMetabolomicsPipelineResults = async(projectId, progressiveId) => {
    try{
        const response = await api.get(`/api/v1/project/${projectId}/pipelines/${progressiveId}/results`);
        console.log('retrieving the report of the pipeline');
        return response.data || [];
    }catch(e){
        console.error('Error in retrieving the results of the current pipeline', e);
        throw new Error('Error in retrieving the results of he current pipeline.');
    }
}


export const fetchMetabolomicsMatrices = async (projectId) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/matrix`);
        console.log('Matrices retrieved:', response.data);
        return response.data || [];
    } catch (err) {
        console.error('Error fetching matrices:', err);
        throw new Error('Error fetching matrices for this project');
    }
};

export const fetchPipelineDetails = async (projectId, pipelineId) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/pipelines/${pipelineId}`);
        console.log('Pipeline details retrieved:', response.data);
        return response.data || {};
    }
    catch (err) {
        console.error('Error fetching pipeline details:', err);
        throw new Error('Error fetching pipeline details');
    }
}


// 🌋 NEW: Fetch Volcano Plot data
export const fetchVolcanoPlotData = async (projectId, pipelineId) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/pipelines/${pipelineId}/volcano_plot/`);
        console.log('Volcano plot data retrieved:', response.data);
        return response.data || [];
    } catch (err) {
        console.error('Error fetching volcano plot data:', err);
        throw new Error('Error fetching volcano plot data for this pipeline');
    }
};