import React, {useEffect, useState} from 'react';
import { useParams } from 'react-router-dom';
import {fetchMetabolomicsPipelines} from '../../services/metabolomics_api';
import MetabolomicsPipelineItem from '../pipelines/MetabolomicsPipelineItem'
import {Box, Typography, CircularProgress, Alert, useTheme} from '@mui/material';
import Navbar from '../Navbar';

const PipelineRunMetabolomicsDashboard = () => {
    const {progressive_id} = useParams();
    const [pipelines, setPipelines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const theme = useTheme();

    useEffect(()=>{
        const getPipelines = async () => {
            try {
                const data = await fetchMetabolomicsPipelines(progressive_id)
                setPipelines(data);
            }catch(err){
                setError('Failed to load pipelines');
            }finally{
                setLoading(false)
            }
        };
        getPipelines();
    }, [progressive_id]);

    if (loading) return <Box display='flex' justifyContent='center' alignItems='center' height='100vh'><CircularProgress/></Box>
    if (error) return <Alert severity='error'>{error}</Alert>

    const handleDeletePipeline = (progressiveId) => {
        setPipelines(prev => prev.filter(p => p.progressive_id !== progressiveId));
    };

    return (
        <>
            <Navbar/>
            <Typography variant='h4' component='h1' gutterBottom align="center" sx={{fontWeight: 700, letterSpacing: 1, mt: 2}}>
                Running Pipelines
            </Typography>
            <Box
                sx={{
                    width: '100%',
                    overflowX: 'auto',
                    py: 3,
                    px: { xs: 1, md: 4 },
                    background: `linear-gradient(90deg, ${theme.palette.grey[100]}, ${theme.palette.grey[200]})`,
                    borderRadius: 3,
                    boxShadow: 2,
                }}
            >
                <Box
                    sx={{
                        display: 'flex',
                        flexDirection: 'row',
                        gap: { xs: 2, md: 4 },
                        minHeight: 340,
                        alignItems: 'stretch',
                    }}
                >
                    {pipelines.length > 0 ? (
                        pipelines.map((pipeline) => (
                            <MetabolomicsPipelineItem
                                key={pipeline.progressive_id}
                                pipeline={pipeline}
                                onDelete={handleDeletePipeline}
                            />
                        ))
                    ) : (
                        <Box display="flex" alignItems="center" justifyContent="center" width="100%">
                            <Typography variant='body1' color='textSecondary'>
                                No running pipelines.
                            </Typography>
                        </Box>
                    )}
                </Box>
            </Box>
        </>
    );
};

export default PipelineRunMetabolomicsDashboard;