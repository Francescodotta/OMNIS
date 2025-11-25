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