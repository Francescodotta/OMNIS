// GatingStrategyForm Component

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Box, TextField, Button, Typography, Paper } from '@mui/material';
import api from '../../utils/ApiFlowCytometry';
import { useNavigate } from 'react-router-dom';

/**
 * GatingStrategyForm component can be used to create a new gating strategy (POST)
 * or update an existing gating strategy (PUT), depending on if a gatingStrategy prop is provided.
 *
 * Props:
 * - gatingStrategy (object): Existing gating strategy data for update. If not provided, form is in creation mode.
 * - flowCytometryId (string): The id of the flow cytometry record to which this gating strategy belongs.
 * - onSuccess (function): Callback to trigger after a successful API call.
 */
const GatingStrategyForm = ({ gatingStrategy = null, flowCytometryId, onSuccess }) => {
  // Set initial form values based on passed gatingStrategy prop (if any).
  const [name, setName] = useState(gatingStrategy ? gatingStrategy.name : '');
  const [description, setDescription] = useState(gatingStrategy ? gatingStrategy.description : '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { projectId, progressiveId } = useParams(); // Updated to remove progressiveId if not needed
  const navigate = useNavigate();
  console.log(flowCytometryId);  

  // Update state if gatingStrategy prop changes.
  useEffect(() => {
    if (gatingStrategy) {
      setName(gatingStrategy.name || '');
      setDescription(gatingStrategy.description || '');
    }
  }, [gatingStrategy]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Prepare payload that respects backend structure.
    const payload = {
      name,
      description,
      // Additional fields like creator and timestamps are expected to be handled on the backend.
    };

    try {
      if (gatingStrategy) {
        console.log(gatingStrategy);
        // Update existing gating strategy (PUT request)
        const response = await api.put(
          `/flow_cytometry/api/v1/project/${projectId}/flow_cytometry/${progressiveId}/gating_strategies/${gatingStrategy.progressive_id}`,
          payload
        );
        // You can handle response.data if needed.
        if (onSuccess) onSuccess(response.data);
      } else {
        console.log(progressiveId);
        // Create new gating strategy (POST request)
        const response = await api.post(
          `/flow_cytometry/api/v1/project/${projectId}/flow_cytometry/${progressiveId}/gating_strategies`,
          payload
        );
        // You can handle response.data if needed.
        if (onSuccess) onSuccess(response.data);
        // navigate to the gating strategies dashboard
        navigate(`/project/${projectId}/fcs_object/${progressiveId}/gatingStrategies`);
      }
    } catch (err) {
      console.error('Error submitting gating strategy:', err);
      setError('An error occurred while saving the gating strategy.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 2 }}>
      <Typography variant="h6" component="h2" gutterBottom>
        {gatingStrategy ? 'Update Gating Strategy' : 'Create Gating Strategy'}
      </Typography>
      <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
        <TextField
          margin="normal"
          required
          fullWidth
          id="name"
          label="Name"
          name="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <TextField
          margin="normal"
          fullWidth
          id="description"
          label="Description"
          name="description"
          multiline
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        {error && (
          <Typography color="error" variant="body2" sx={{ mt: 1 }}>
            {error}
          </Typography>
        )}
        <Button
          type="submit"
          fullWidth
          variant="contained"
          color="primary"
          disabled={loading}
          sx={{ mt: 3 }}
        >
          {gatingStrategy ? 'Update' : 'Create'}
        </Button>
      </Box>
    </Paper>
  );
};

export default GatingStrategyForm;