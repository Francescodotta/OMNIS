import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Paper, Button, List, ListItem, ListItemText, ListItemSecondaryAction, IconButton, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { Delete as DeleteIcon, Visibility as VisibilityIcon } from '@mui/icons-material';
import api from '../utils/ApiMetabolomics'; // Assicurati di importare il pacchetto api configurato
import PipelineDetails from '../components/PipelineDetails';

const HandlePipeline = () => {
  const { progressive_id: projectId } = useParams(); // Ottieni projectId dai parametri della route
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // Effettua una GET request per ottenere le pipeline salvate per il progetto specifico
    api.get(`/api/project/${projectId}/pipelines`)
      .then((response) => {
        setPipelines(response.data);
      })
      .catch((error) => {
        console.error('Error loading pipelines:', error);
      });
  }, [projectId]);

  const handleViewDetails = (pipeline) => {
    setSelectedPipeline(pipeline);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedPipeline(null);
  };

  const handleDelete = (pipelineId) => {
    // Effettua una DELETE request per eliminare la pipeline
    api.delete(`/api/project/${projectId}/pipelines/${pipelineId}`)
      .then(() => {
        setPipelines((prevPipelines) => prevPipelines.filter((pipeline) => pipeline.progressive_id !== pipelineId));
      })
      .catch((error) => {
        console.error('Error deleting pipeline:', error);
      });
  };

  return (
    <Box sx={{ padding: 2 }}>
      <Typography variant="h4" gutterBottom>
        Manage Pipelines
      </Typography>
      <Paper sx={{ padding: 2 }}>
        <List>
          {pipelines.map((pipeline) => (
            <ListItem key={pipeline.progressive_id} button onClick={() => handleViewDetails(pipeline)}>
              <ListItemText 
                primary={`Pipeline Name: ${pipeline.name}`} // Display the pipeline name
                secondary={`Project ID: ${pipeline.project_id}`} 
              />
              <ListItemSecondaryAction>
                <IconButton edge="end" aria-label="view" onClick={() => handleViewDetails(pipeline)}>
                  <VisibilityIcon />
                </IconButton>
                <IconButton edge="end" aria-label="delete" onClick={() => handleDelete(pipeline.progressive_id)}>
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </Paper>
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>Pipeline Details</DialogTitle>
        <DialogContent>
          {selectedPipeline && (
            <Box>
              <Typography variant="h6">Pipeline Steps</Typography>
              <List>
                {selectedPipeline.pipeline.steps.map((step, index) => (
                  <ListItem key={index}>
                    <ListItemText 
                      primary={`Step Name: ${step.name}`} 
                      secondary={`Parameters: ${JSON.stringify(step.parameters)}`} // Display parameters as JSON
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HandlePipeline;