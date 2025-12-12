import React, {useEffect, useState} from 'react';
import {useParams} from 'react-router-dom';
import {fetchProteomicsPipelines} from '../../../services/proteomics_api';
import ProteomicsPipelineElement from './ProteomicsPipeline';
import {Box, Typography, CircularProgress, Alert, useTheme} from '@mui/material';
import Navbar from '../../Navbar';

const ProteomicsPipelineResultsDashboard = () => {
    const {projectId} = useParams();
    const [pipelines, setPipelines]= useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const theme = useTheme();


    // use the fetching of the entire proteomics pipelines from the backend 
    useEffect(() => {
        const getPipelines = async () => {
            try{
                const data = await fetchProteomicsPipelines(projectId)
                console.log(data);
                setPipelines(data);
            }catch(err){
                setError('Failed to load pipelines from the proteomics microservice')     
            }finally{
                setLoading(false)
            }
        };
        getPipelines();
    }, [projectId]);

    if (loading) return <Box display='flex' justifyContent='center' alignItems='center' height='100vh'><CircularProgress/></Box> 
    if (error) return <Alert severity='error'>{error}</Alert>


    // handle the deletion of the pipeline 
    const handleDeletePipeline = (progressiveId) => {
        setPipelines(prev => prev.filter(p => p.progressive_id !== progressiveId))
    } 

    return (
        <>
        <Navbar/>
        <Typography variant='h4' component='h1' gutterBottom align='center' sx={{fontWeight: 700, letterSpacing: 1, mt: 2}}>
            Running Proteomics Pipelines
        </Typography>
        {/* FIRST BOX */}
        <Box sx={{width:'100%', overflowX:'auto', py:3, px:{xs:1, md:4},
                background:`linear-gradient(90deg, ${theme.palette.grey[100]}, ${theme.palette.grey[200]})`,
                borderRadius:3, boxShadow:2}}>
            
            {/* SECOND BOX */}
            <Box sx={{display:'flex', flexDirection:'row', gap: {xs:2, md:4}, minHeight:340, alignItems:'stretch',}}>
                {/*   ITERATE OVER THE LIST OF PIPELINES FETCHED BY THE BACKEND SERVER */}
                {pipelines.length > 0 ? (
                    pipelines.map((pipeline) => (
                        <ProteomicsPipelineElement key={pipeline.progressive_id} pipeline={pipeline} onDelete={handleDeletePipeline}/>
                        
                    ))
                ): (
                    <Box display="flex" alignItems="center" justifyContent="center" width="100%">
                        <Typography variant='body1' color='textSecondary'>
                            No running pipelines.
                        </Typography>
                    </Box>
                )}
                {/* THIRD BOX -- IF NO RUNNING PIPELINES ARE AVAILABLE FROM THE BACKEND */}

            </Box>
        </Box>
        
        
        </>
    )



}


export default ProteomicsPipelineResultsDashboard