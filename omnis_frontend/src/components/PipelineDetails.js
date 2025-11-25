import React from 'react';
import { Box, Typography, List, ListItem, ListItemText } from '@mui/material';

const PipelineDetails = ({ pipeline }) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Pipeline {pipeline.progressive_id}
      </Typography>
      <List>
        {pipeline.pipeline.map((step, index) => (
          <ListItem key={index}>
            <ListItemText primary={`Step ${index + 1}: ${step.pipeline_name}`} secondary={`Parameters: ${JSON.stringify(step.parameters)}`} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default PipelineDetails;