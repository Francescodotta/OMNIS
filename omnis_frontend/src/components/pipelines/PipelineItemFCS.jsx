import React from 'react';
import { Box, Typography, List, ListItem, ListItemText, Button, Chip } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { deletePipeline } from '../../services/fcs_api'; // Import the delete function

const PipelineItemFCS = ({ pipeline, onDelete }) => {
    const navigate = useNavigate();

    const handleViewReport = () => {
        // Navigate to the report page or perform any other action
        navigate(`/project/${pipeline.project_id}/flow_cytometry/report/${pipeline.progressive_id}`);
    };

    const handleDeletePipeline = async () => {
        try {
            await deletePipeline(pipeline.project_id, pipeline.progressive_id);
            if (onDelete) {
                onDelete(pipeline.progressive_id); // Notify parent component to update the list
            }
        } catch (error) {
            console.error('Error deleting pipeline:', error);
            alert('Failed to delete the pipeline. Please try again.');
        }
    };

    const getFileName = (filePath) => {
        return filePath.split('/').pop();
    };

    // Determine pipeline status
    const pipelineStatus = pipeline.status || "unknown"; // Default to "unknown" if status is missing
    const statusColor =
        pipelineStatus === "completed"
            ? "success"
            : pipelineStatus === "in_progress"
            ? "warning"
            : "error";

    // Function to determine the color of step status
    const getStepStatusColor = (status) => {
        switch (status) {
            case "waiting":
                return "black";
            case "completed":
                return "green";
            case "failed":
                return "red";
            case "in_progress":
                return "blue";
            default:
                return "gray"; // Default color for unknown statuses
        }
    };

    return (
        <Box 
            border={1} 
            borderRadius={4} 
            p={2} 
            mb={2} 
            width="100%" 
            maxWidth="600px" 
            mx="auto" 
            boxShadow={3}
        >
            {/* Pipeline Title */}
            <Typography variant="h6" component="h2">
                Pipeline Name: {pipeline.name}
            </Typography>

            {/* Pipeline Status */}
            <Box sx={{ mb: 2 }}>
                <Chip
                    label={`Status: ${pipelineStatus}`}
                    color={statusColor}
                    variant="outlined"
                />
            </Box>

            {/* Pipeline Details */}
            <Typography variant="body1">
                Chain ID: {pipeline.chain_id}
            </Typography>
            <Typography variant="body1">
                Project ID: {pipeline.project_id}
            </Typography>
            <Typography variant="body1">
                Progressive ID: {pipeline.progressive_id}
            </Typography>

            {/* Steps and their statuses */}
            <Typography variant="body1" component="div" sx={{ mt: 2 }}>
                Steps:
                <List>
                    {pipeline.step_statuses &&
                        Object.entries(pipeline.step_statuses).map(([stepName, stepStatus], index) => (
                            <ListItem key={index}>
                                <ListItemText
                                    primary={stepName}
                                    secondary={
                                        <span style={{ color: getStepStatusColor(stepStatus) }}>
                                            Status: {stepStatus}
                                        </span>
                                    }
                                />
                            </ListItem>
                        ))}
                </List>
            </Typography>

            {/* Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Button variant="contained" color="primary" onClick={handleViewReport}>
                    View Report
                </Button>
                <Button variant="outlined" color="error" onClick={handleDeletePipeline}>
                    Delete Pipeline
                </Button>
            </Box>
        </Box>
    );
};

export default PipelineItemFCS;