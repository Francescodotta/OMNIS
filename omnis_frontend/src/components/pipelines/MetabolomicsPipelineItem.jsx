import React from 'react';
import {
    Typography, List, ListItem, ListItemText, Button, Stack, Paper, Chip, Divider, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { deleteMetabolomicsPipeline } from '../../services/metabolomics_api';
import PlayCircleOutlineIcon from '@mui/icons-material/PlayCircleOutline';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import DescriptionIcon from '@mui/icons-material/Description';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const MetabolomicsPipelineItem = ({ pipeline, onDelete }) => {
    const navigate = useNavigate();

    const handleViewReport = () => {
        navigate(`/project/${pipeline.project_id}/metabolomics/pipeline/${pipeline.progressive_id}/report`);
    };

    const handleDeletePipeline = async () => {
        try {
            await deleteMetabolomicsPipeline(pipeline.project_id, pipeline.progressive_id);
            if (onDelete) {
                onDelete(pipeline.progressive_id);
            }
        } catch (error) {
            console.error("Failed to delete pipeline:", error);
        }
    };

    return (
        <Paper
            elevation={6}
            sx={{
                borderRadius: 5,
                p: 2.2,
                minWidth: 320,
                maxWidth: 350,
                width: { xs: 260, sm: 320, md: 340 },
                boxShadow: 6,
                background: 'linear-gradient(135deg, #f8fafc 60%, #e3e7ed 100%)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
                alignItems: 'stretch',
                transition: 'transform 0.2s',
                gap: 0.7, // reduced gap
                '&:hover': {
                    transform: 'scale(1.03)',
                    boxShadow: 12,
                },
            }}
        >
            <Stack direction="row" alignItems="center" spacing={1} mb={0.3}>
                <DescriptionIcon color="primary" />
                <Typography variant='h6' component='h2' sx={{ fontWeight: 600 }}>
                    {pipeline.name || `Pipeline #${pipeline.progressive_id}`}
                </Typography>
            </Stack>
            <Divider sx={{mb: 0.7}} />
            <Stack direction="row" spacing={1} mb={0.7}>
                <Chip label={`Project: ${pipeline.project_id}`} color="info" size="small" />
                <Chip label={`Task: ${pipeline.task_id?.slice(0, 8) || '-'}`} color="default" size="small" />
            </Stack>
            <Accordion sx={{ boxShadow: 'none', background: 'transparent', mb: 1 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: 28, px: 0 }}>
                    <Typography variant='subtitle2' color="text.secondary" sx={{ fontWeight: 500 }}>
                        Steps
                    </Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ px: 0, py: 0 }}>
                    <List dense sx={{ mb: 0, pl: 1, py: 0 }}>
                        {pipeline.pipeline_data?.pipeline?.steps?.map((step, index) => (
                            <ListItem
                                key={index}
                                sx={{
                                    py: 0,
                                    minHeight: 20,
                                    '& .MuiListItemText-root': { m: 0 }
                                }}
                                disableGutters
                            >
                                <ListItemText
                                    primary={step.name}
                                    primaryTypographyProps={{ fontSize: 13 }}
                                />
                            </ListItem>
                        ))}
                    </List>
                </AccordionDetails>
            </Accordion>
            <Stack direction="row" spacing={2} justifyContent="center" pt={0.5} mt={0.5}>
                <Button
                    variant='contained'
                    color='primary'
                    startIcon={<PlayCircleOutlineIcon />}
                    onClick={handleViewReport}
                    sx={{ fontWeight: 600, px: 2, minWidth: 110 }}
                >
                    View Report
                </Button>
                <Button
                    variant='outlined'
                    color='error'
                    startIcon={<DeleteOutlineIcon />}
                    onClick={handleDeletePipeline}
                    sx={{ fontWeight: 600, px: 2, minWidth: 110 }}
                >
                    Delete
                </Button>
            </Stack>
        </Paper>
    );
};

export default MetabolomicsPipelineItem;