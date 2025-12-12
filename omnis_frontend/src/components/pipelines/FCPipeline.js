import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  Controls,
  useReactFlow,
} from 'react-flow-renderer';
import api from '../../../utils/ApiFlowCytometry';
import { useParams } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Button, 
  TextField, 
  List, 
  ListItem, 
  ListItemText,
  Chip,
  Divider
} from '@mui/material';
import NodeSidebar from '../NodeSidebar';

const initialNodes = [
  {
    id: '1',
    type: 'select_fcs_files',
    data: {
      label: 'Select FCS Files',
      parameters: [{ name: 'file_paths', label: 'FCS Files', type: 'files' }],
    },
    position: { x: 250, y: 0 },
  },
];

const initialEdges = [];

const sidebarStyles = {
  display: 'flex',
  flexDirection: 'column',
  padding: '10px',
  width: '300px',
  backgroundColor: '#e0e0e0',
  borderRight: '1px solid #ddd',
  overflowY: 'auto',
};

const onDragStart = (event, nodeType) => {
  event.dataTransfer.setData('application/reactflow', nodeType);
  event.dataTransfer.effectAllowed = 'move';
};

function FCPipeline() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [availableNodes, setAvailableNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const { project } = useReactFlow();
  const { progressive_id } = useParams();
  const [pipelineName, setPipelineName] = useState('');

  // ✅ SOLO file esistenti nel database
  const [existingFcsFiles, setExistingFcsFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(true);

  // ✅ Fetch dei file FCS dal database
  useEffect(() => {
    const fetchFcsFiles = async () => {
      setLoadingFiles(true);
      try {
        const response = await api.get(
          `/api/v1/project/${progressive_id}/flow_cytometry`
        );
        setExistingFcsFiles(response.data.data || []);
        console.log('Loaded FCS files:', response.data.data);
      } catch (error) {
        console.error('Error fetching FCS files:', error);
      } finally {
        setLoadingFiles(false);
      }
    };

    if (progressive_id) {
      fetchFcsFiles();
    }
  }, [progressive_id]);

  // ✅ Carica i nodi disponibili
  useEffect(() => {
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

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

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
          label: `${nodeType} Node`, 
          parameters: nodeData ? nodeData.parameters : [] 
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
        node.id === nodeId 
          ? { ...node, data: { ...node.data, parameters } } 
          : node
      )
    );
  };

  const getActivePipeline = () => {
    const nodeMap = new Map(nodes.map(node => [node.id, node]));
    const edgeMap = new Map(edges.map(edge => [edge.source, edge.target]));

    const pipeline = [];
    let currentNode = nodeMap.get('1');
    let nodeIndex = 1;

    while (currentNode) {
      const filteredParameters = Object.entries(currentNode.data.parameters || {}).reduce(
        (acc, [key, value]) => {
          if (!isNaN(key)) return acc;
          return { ...acc, [key]: value };
        }, 
        {}
      );

      pipeline.push({ 
        ...currentNode, 
        index: nodeIndex, 
        data: { ...currentNode.data, parameters: filteredParameters } 
      });
      
      const nextNodeId = edgeMap.get(currentNode.id);
      currentNode = nodeMap.get(nextNodeId);
      nodeIndex++;
    }

    return pipeline;
  };

  const handleRunPipeline = async () => {
    const activePipeline = getActivePipeline();
    console.log('Active Pipeline:', activePipeline);

    try {
      const response = await api.post(
        `/api/v1/project/${progressive_id}/process_pipeline`, 
        { pipeline: activePipeline }
      );

      console.log('Pipeline executed successfully:', response.data);
    } catch (error) {
      console.error('Error running pipeline:', error.message);
    }
  };

  const handleSavePipeline = async () => {
    const activePipeline = getActivePipeline();
    console.log('Saving Pipeline:', activePipeline);

    try {
      const response = await api.post(
        `/api/v1/project/${progressive_id}/pipeline`, 
        { 
          pipeline: activePipeline,
          name: pipelineName 
        }
      );

      console.log('Pipeline saved successfully:', response.data);
    } catch (error) {
      console.error('Error saving pipeline:', error.message);
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* ✅ SIDEBAR: Solo visualizzazione file + nodi */}
      <Box style={sidebarStyles}>
        
        {/* Pipeline Name */}
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
            size="small"
          />
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* ✅ SEZIONE: File FCS Disponibili (SOLO VISUALIZZAZIONE) */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" color="primary" sx={{ mb: 1 }}>
            📁 Available FCS Files
          </Typography>
          
          {loadingFiles ? (
            <Typography variant="body2" color="text.secondary">
              Loading files...
            </Typography>
          ) : existingFcsFiles.length > 0 ? (
            <>
              <Chip 
                label={`${existingFcsFiles.length} files`} 
                color="primary" 
                size="small"
                sx={{ mb: 1 }}
              />
              <List dense sx={{ maxHeight: '200px', overflowY: 'auto' }}>
                {existingFcsFiles.map((file, idx) => (
                  <ListItem key={idx} sx={{ py: 0.5 }}>
                    <ListItemText 
                      primary={file.filename || file.name}
                      primaryTypographyProps={{ variant: 'body2' }}
                      secondary={
                        file.uploaded_at 
                          ? new Date(file.uploaded_at).toLocaleDateString() 
                          : null
                      }
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No FCS files found. Please upload files from the project page.
            </Typography>
          )}
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* ✅ Nodi Draggabili */}
        <Typography variant="h6" sx={{ mb: 1 }}>
          Processing Nodes
        </Typography>
        {availableNodes.map((node) => (
          <Button
            key={node.id}
            variant="outlined"
            onDragStart={(event) => onDragStart(event, node.name)}
            draggable
            fullWidth
            sx={{ mt: 1, textTransform: 'none' }}
          >
            {node.name}
          </Button>
        ))}

        <Divider sx={{ my: 2 }} />

        {/* ✅ Pipeline Actions */}
        <Button
          variant="contained"
          color="primary"
          onClick={handleRunPipeline}
          fullWidth
          sx={{ mb: 1 }}
        >
          Run Pipeline
        </Button>
        <Button
          variant="outlined"
          color="primary"
          onClick={handleSavePipeline}
          fullWidth
        >
          Save Pipeline
        </Button>
      </Box>

      {/* ✅ React Flow Canvas */}
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
          style={{ background: '#f0f0f0', borderRadius: '8px' }}
        >
          <Controls />
        </ReactFlow>
      </Box>

      {/* ✅ Node Parameters Sidebar */}
      {selectedNode && (
        <NodeSidebar 
          selectedNode={selectedNode} 
          onSave={handleSaveParameters}
          availableFiles={existingFcsFiles} // ✅ Passa i file per la selezione nei parametri
        />
      )}
    </Box>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <FCPipeline />
    </ReactFlowProvider>
  );
}