import React, { useState, useCallback } from 'react';
import ReactFlow, { ReactFlowProvider, addEdge, useNodesState, useEdgesState, Controls } from 'react-flow-renderer';
import { Box, Button, TextField, Typography } from '@mui/material';
import NodeSidebar from '../components/NodeSidebar';

const initialNodes = [
  { id: '1', type: 'input', data: { label: 'Start Node' }, position: { x: 250, y: 5 } }
];

const initialEdges = [];

const PipelineBuilder = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [pipelineName, setPipelineName] = useState('');

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const nodeType = event.dataTransfer.getData('application/reactflow');
      const position = { x: event.clientX, y: event.clientY };
      const newNode = { id: `${nodes.length + 1}`, type: nodeType, position, data: { label: `${nodeType} Node` } };
      setNodes((nds) => nds.concat(newNode));
    },
    [nodes, setNodes]
  );

  const onDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  };

  const handleSavePipeline = async () => {
    try {
      const response = await fetch('/api/project/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: pipelineName, pipeline: nodes })
      });
      if (!response.ok) throw new Error('Failed to save pipeline');
      console.log('Pipeline saved successfully');
    } catch (error) {
      console.error(error.message);
    }
  };

  return (
    <ReactFlowProvider>
      <Box sx={{ display: 'flex', height: '100vh' }}>
        <Box sx={{ width: 250, padding: 2, backgroundColor: '#e0e0e0' }}>
          <Typography variant="h6">Pipeline Name</Typography>
          <TextField
            fullWidth
            label="Enter pipeline name"
            variant="outlined"
            value={pipelineName}
            onChange={(e) => setPipelineName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Button variant="contained" color="primary" onClick={handleSavePipeline} sx={{ mt: 2 }}>Save Pipeline</Button>
        </Box>
        <Box sx={{ flex: 1, height: '100%' }} onDrop={onDrop} onDragOver={onDragOver}>
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect}>
            <Controls />
          </ReactFlow>
        </Box>
      </Box>
    </ReactFlowProvider>
  );
};

export default PipelineBuilder;
