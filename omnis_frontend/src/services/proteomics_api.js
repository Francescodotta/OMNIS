import api from '../utils/ApiProteomics';

export const fetchProteomicsPipelines = async(projectId) => {
    try{
        const response = await api.get(`/api/v1/project/${projectId}/pipeline`)
        console.log(response)
        return response.data || [];
    }catch(e){
        console.log('Error fetching the proteomics pipelines: ', e)
        throw new Error('Error fetching the metabolomics pipelines')
    }
}


export const deleteProteomicsPipeline = async(projectId, pipelineId) => {
    try{
        const response = await api.delete(`api/v1/project/${projectId}/pipeline/${pipelineId}`)
        return response.data || []
    }catch(e){
        console.log('Error in deleting the pipeline', e);
        throw new Error('Error in deleting the proteomics pipeline')
    }
}