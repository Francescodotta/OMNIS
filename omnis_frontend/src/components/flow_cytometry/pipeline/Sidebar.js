// omnis_frontend/src/components/pipelines/Sidebar.js

import React, { useState } from 'react';
import { Box, Typography, Button, TextField, Collapse, IconButton } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const sidebarStyles = {
  display: 'flex',
  flexDirection: 'column',
  padding: '10px',
  width: '250px',
  backgroundColor: '#e0e0e0',
  borderRight: '1px solid #ddd',
  overflowY: 'auto',
};

const Sidebar = ({
  onDragStart,
  handleRunPipeline,
  handleSavePipeline,
  pipelineName,
  setPipelineName,
  availableNodes,
}) => {
  const [nodesExpanded, setNodesExpanded] = useState(true);

  const toggleNodes = () => {
    setNodesExpanded(!nodesExpanded);
  };

  return (
    <Box style={sidebarStyles}>
      {/* Pipeline Name Input */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Pipeline Name
        </Typography>
        <TextField
          fullWidth
          label="Enter pipeline name"
          variant="outlined"
          value={pipelineName}
          onChange={(e) => setPipelineName(e.target.value)}
          sx={{ mb: 2 }}
        />
      </Box>

      {/* Available Nodes Section with Collapsible Menu */}
      <Box sx={{ mb: 2 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            '&:hover': { backgroundColor: '#d0d0d0' },
            p: 1,
            borderRadius: 1,
          }}
          onClick={toggleNodes}
        >
          <Typography variant="h6">Available Nodes</Typography>
          <IconButton size="small">
            {nodesExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
        <Collapse in={nodesExpanded}>
          <Box sx={{ mt: 1 }}>
            {availableNodes.map((node) => (
              <Button
                key={node.id}
                variant="outlined"
                onDragStart={(event) => onDragStart(event, node.name)}
                draggable
                sx={{ mt: 1, width: '100%' }}
              >
                {node.label}
              </Button>
            ))}
          </Box>
        </Collapse>
      </Box>

      {/* Run and Save Pipeline Buttons */}
      <Button
        variant="contained"
        color="primary"
        onClick={handleRunPipeline}
        sx={{ mt: 2 }}
      >
        Run Pipeline
      </Button>
      {/* <Button
        variant="contained"
        color="primary"
        onClick={handleSavePipeline}
        sx={{ mt: 2 }}
      >
        Save Pipeline
      </Button> */}
    </Box>
  );
};

export default Sidebar;