// omnis_frontend/src/components/pipelines/FCPipeline.js

import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  Controls,
  useReactFlow,
  getIncomers,
  getOutgoers,
  getConnectedEdges,
} from 'react-flow-renderer';
import { Box, Snackbar, Alert } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import NodeParameterPanel from './NodeParameterPanel';
import api from '../../../utils/ApiFlowCytometry';

const initialNodes = [
  {
    id: '1',
    type: 'select_fcs_files',
    data: {
      label: 'Select FCS Files',
      parameters: [{ name: 'files', label: 'FCS Files', type: 'text' }],
    },
    position: { x: 250, y: 0 },
  },
];

const initialEdges = [];

function FCPipeline() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [availableNodes, setAvailableNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const { project } = useReactFlow();
  const progressive_id = useParams(); // Project ID
  const [pipelineName, setPipelineName] = useState('');
  const [fcsFiles, setFcsFiles] = useState([]); // Define fcsFiles state
  
  // 🦍 NEW: State for notifications and navigation
  const navigate = useNavigate();
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info', // 'success', 'error', 'warning', 'info'
  });

  // 🦍 NEW: Helper function to show notifications
  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  // 🦍 NEW: Helper function to close notifications
  const handleCloseNotification = (event, reason) => {
    if (reason === 'clickaway') return;
    setNotification({ ...notification, open: false });
  };

  useEffect(() => {
    // Load nodes from JSON file and filter only Flow Cytometry nodes
    fetch('/forms/processing_functions.json')
      .then((response) => response.json())
      .then((data) => {
        const flowCytometryNodes = data.functions.filter(
          (node) => node.field === 'Flow Cytometry'
        );
        setAvailableNodes(flowCytometryNodes);
      })
      .catch((error) => console.error('Error loading nodes:', error));
  }, []);

  useEffect(() => {
    // Fetch the list of FCS files for the project
    const fetchFcsFiles = async () => {
      try {
        const response = await api.get(
          `/flow_cytometry/api/v1/project/${progressive_id.progressive_id}/flow_cytometry`
        );
        setFcsFiles(response.data.data || []);
        console.log('Fetched FCS Files:', response.data.data);
      } catch (error) {
        console.error('Error fetching FCS files:', error);
      }
    };

    fetchFcsFiles();
  }, [progressive_id.progressive_id]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const nodeType = event.dataTransfer.getData('application/reactflow');
      const position = project({ x: event.clientX, y: event.clientY });
      const nodeData = availableNodes.find((node) => node.name === nodeType);
      const newNode = {
        id: (nodes.length + 1).toString(),
        type: nodeType,
        position,
        data: {
          label: nodeData ? nodeData.label : `${nodeType} Node`, // Use node.label for display
          name: nodeType, // Store node.name for backend
          parameters: nodeData ? nodeData.parameters : [],
        },
      };
      setNodes((nds) => nds.concat(newNode));
    },
    [nodes, setNodes, availableNodes, project]
  );

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const onDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  };

  const handleSaveParameters = (nodeId, parameters) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, parameters } } : node
      )
    );
  };

  // Prevent deletion of the node with id '1'
  const onNodesDelete = useCallback(
    (deleted) => {
      const filteredNodes = deleted.filter((node) => node.id !== '1');
      if (filteredNodes.length !== deleted.length) {
        alert('The "Select FCS Files" node cannot be removed.');
      }

      setEdges(
        filteredNodes.reduce((acc, node) => {
          const incomers = getIncomers(node, nodes, edges);
          const outgoers = getOutgoers(node, nodes, edges);
          const connectedEdges = getConnectedEdges([node], edges);

          const remainingEdges = acc.filter(
            (edge) => !connectedEdges.includes(edge)
          );

          const createdEdges = incomers.flatMap(({ id: source }) =>
            outgoers.map(({ id: target }) => ({
              id: `${source}->${target}`,
              source,
              target,
            }))
          );

          return [...remainingEdges, ...createdEdges];
        }, edges)
      );

      setNodes((nds) => nds.filter((node) => !filteredNodes.includes(node)));
    },
    [nodes, edges, setEdges, setNodes]
  );

  // Function to get the active pipeline
  const getActivePipeline = () => {
    const nodeMap = new Map(nodes.map((node) => [node.id, node]));
    const edgeMap = new Map(edges.map((edge) => [edge.source, edge.target]));

    const pipeline = [];
    let currentNode = nodeMap.get('1'); // Start from the initial node
    let nodeIndex = 1;

    while (currentNode) {
      // Filter node parameters to keep only keys that are not numeric
      const filteredParameters = Object.entries(currentNode.data.parameters || {}).reduce(
        (acc, [key, value]) => {
          if (!isNaN(key)) {
            return acc;
          }
          return { ...acc, [key]: value };
        }, {}
      );

      pipeline.push({
        id: currentNode.id,
        type: currentNode.data.name || currentNode.type,
        index: nodeIndex,
        data: {
          parameters: filteredParameters,
        },
        position: currentNode.position,
      });
      const nextNodeId = edgeMap.get(currentNode.id);
      currentNode = nodeMap.get(nextNodeId);
      nodeIndex++;
    }

    return pipeline;
  };

  // Function to handle "Run Pipeline" button click
  const handleRunPipeline = async () => {
    if (!pipelineName) {
      showNotification('Please enter a name for the pipeline.', 'warning');
      return;
    }

    const activePipeline = getActivePipeline();
    console.log('Active Pipeline:', activePipeline);

    // Send the pipeline to the backend
    try {
      const response = await api.post(
        `/flow_cytometry/api/v1/project/${progressive_id.progressive_id}/process_pipeline`,
        {
          body: JSON.stringify({ pipeline: activePipeline, name: pipelineName }),
        }
      );

      if (response.status === 200) {
        // 🦍 SUCCESS: Show success message and redirect
        showNotification('Pipeline started successfully! Redirecting...', 'success');
        
        // Redirect to running pipelines page after 1.5 seconds
        setTimeout(() => {
          navigate(`/project/${progressive_id.progressive_id}/running_pipelines`);
        }, 1500);
      } else {
        // 🦍 ERROR: Handle non-200 responses
        const errorData = response.data;
        const errorMessage = errorData?.message || errorData?.error || 'An unexpected error occurred while starting the pipeline.';
        showNotification(`Error: ${errorMessage}`, 'error');
      }
    } catch (error) {
      // 🦍 ERROR: Handle network/API errors
      console.error('Error running pipeline:', error);
      
      let errorMessage = 'Failed to start pipeline. Please try again.';
      
      if (error.response) {
        // Server responded with an error
        const serverError = error.response.data;
        errorMessage = serverError?.message || serverError?.error || `Server error: ${error.response.status}`;
      } else if (error.request) {
        // Request was made but no response received
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        // Error in setting up the request
        errorMessage = error.message || 'An unexpected error occurred.';
      }
      
      showNotification(errorMessage, 'error');
    }
  };

  const handleSavePipeline = async () => {
    if (!pipelineName) {
      showNotification('Please enter a name for the pipeline.', 'warning');
      return;
    }

    const activePipeline = getActivePipeline();
    console.log('Active Pipeline:', activePipeline);

    // Send the pipeline to the backend with the pipeline name
    try {
      const response = await api.post(
        `/flow_cytometry/api/v1/project/${progressive_id.progressive_id}/pipeline`,
        {
          body: JSON.stringify({
            pipeline: activePipeline,
            name: pipelineName,
          }),
        }
      );

      if (response.status === 200) {
        // 🦍 SUCCESS: Show success message and redirect
        showNotification('Pipeline saved successfully! Redirecting...', 'success');
        
        // Redirect to pipelines page after 1.5 seconds
        setTimeout(() => {
          navigate(`/project/${progressive_id.progressive_id}/pipelines`);
        }, 1500);
      } else {
        // 🦍 ERROR: Handle non-200 responses
        const errorData = response.data;
        const errorMessage = errorData?.message || errorData?.error || 'An unexpected error occurred while saving the pipeline.';
        showNotification(`Error: ${errorMessage}`, 'error');
      }
    } catch (error) {
      // 🦍 ERROR: Handle network/API errors
      console.error('Error saving pipeline:', error);
      
      let errorMessage = 'Failed to save pipeline. Please try again.';
      
      if (error.response) {
        const serverError = error.response.data;
        errorMessage = serverError?.message || serverError?.error || `Server error: ${error.response.status}`;
      } else if (error.request) {
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        errorMessage = error.message || 'An unexpected error occurred.';
      }
      
      showNotification(errorMessage, 'error');
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar
        onDragStart={onDragStart}
        handleRunPipeline={handleRunPipeline}
        handleSavePipeline={handleSavePipeline}
        pipelineName={pipelineName}
        setPipelineName={setPipelineName}
        availableNodes={availableNodes}
      />
      <Box
        sx={{
          flex: 1,
          height: '100%',
          padding: 2,
          backgroundColor: '#f0f0f0',
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onNodesDelete={onNodesDelete}
          style={{ background: '#f0f0f0', borderRadius: '8px' }}
        >
          <Controls />
        </ReactFlow>
      </Box>
      <NodeParameterPanel
        selectedNode={selectedNode}
        onSave={handleSaveParameters}
        fcsFiles={fcsFiles}
      />
      
      {/* 🦍 NEW: Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

// Wrap FCPipeline in ReactFlowProvider and export the component
export default function App() {
  return (
    <ReactFlowProvider>
      <FCPipeline />
    </ReactFlowProvider>
  );
}