// Importa i pacchetti necessari
import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  Controls,
  useReactFlow,
} from 'react-flow-renderer';
import { useParams } from 'react-router-dom';
import { Box, Typography, Paper, Button, TextField } from '@mui/material';
import NodeSidebar from './NodeSidebar';
import api from '../utils/ApiMetabolomics'; // Assicurati di importare il pacchetto api configurato

const initialNodes = [
  {
    id: '1',
    type: 'select_files',
    data: { label: 'Select files', parameters: [{name:"files", label:"Files", type:"text"}] },
    position: { x: 250, y: 0 },
  },
];

const initialEdges = [];

// Definisce lo stile per l'area di drag-and-drop
const sidebarStyles = {
  display: 'flex',
  flexDirection: 'column',
  padding: '10px',
  width: '150px',
  backgroundColor: '#e0e0e0',
  borderRight: '1px solid #ddd',
};

// Nodo da usare per il drag
const onDragStart = (event, nodeType) => {
  event.dataTransfer.setData('application/reactflow', nodeType);
  event.dataTransfer.effectAllowed = 'move';
};

function DiagramDragDrop() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [availableNodes, setAvailableNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [metabolomicsExperiments, setMetabolomicsExperiments] = useState([]);
  const {project} = useReactFlow();
  const progressive_id = useParams(); // ID del progetto
  const [pipelineName, setPipelineName] = useState(''); // Stato per il nome della pipeline

  useEffect(() => {
    // Carica i nodi dal file JSON
    fetch('/forms/processing_functions.json')
      .then((response) => response.json())
      .then((data) => {
        setAvailableNodes(data.functions);
      })
      .catch((error) => console.error('Error loading nodes:', error));
  }, []);

  useEffect(() => {
    // Effettua una GET request per ottenere gli esperimenti di metabolomica
    api.get(`/api/project/${progressive_id.progressive_id}/metabolomics`)
      .then((response) => {
        setMetabolomicsExperiments(response.data);
      })
      .catch((error) => {
        console.error('Error loading metabolomics experiments:', error);
      });
  }, [progressive_id.progressive_id]);

  // Gestisce la creazione di nuove connessioni tra nodi
  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Gestisce il rilascio di un nuovo nodo nell'area di diagramma
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
        data: { label: `${nodeType} Node`, parameters: nodeData ? nodeData.parameters : [] },
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

  // Funzione per ottenere la pipeline attiva
  const getActivePipeline = () => {
    const nodeMap = new Map(nodes.map(node => [node.id, node]));
    const edgeMap = new Map(edges.map(edge => [edge.source, edge.target]));

    const pipeline = [];
    let currentNode = nodeMap.get('1'); // Partiamo dal nodo di start
    let nodeIndex = 1;

    while (currentNode) {
      // Filtra i parametri del nodo per mantenere solo quelli con chiavi non numeriche
      const filteredParameters = Object.entries(currentNode.data.parameters || {}).reduce(
        (acc, [key, value]) => {
          if (!isNaN(key)) {
            return acc;
          }
          return { ...acc, [key]: value };
        }, 
        {}
      );

      pipeline.push({ ...currentNode, index: nodeIndex, data: { ...currentNode.data, parameters: filteredParameters } });
      const nextNodeId = edgeMap.get(currentNode.id);
      currentNode = nodeMap.get(nextNodeId);
      nodeIndex++;
    }

    return pipeline;
  };

  // Funzione per gestire il click del tasto "Run Pipeline"
  const handleRunPipeline = async () => {
    const activePipeline = getActivePipeline();
    console.log('Active Pipeline:', activePipeline);

    // Invia la pipeline al backend
    try {
      const response = await api.post(`/api/project/${progressive_id.progressive_id}/process_pipeline`, {
        body: JSON.stringify({ pipeline: activePipeline }),
      });

      if (response.status !== 200) {
        const errorData = await response.json();
        throw new Error(`Network response was not ok: ${errorData.message}`);
      }

      const result = response.data;
      console.log('Pipeline saved successfully:', result);
    } catch (error) {
      console.error('Error saving pipeline:', error.message);
    }
  };

  const handleSavePipeline = async () => {
    const activePipeline = getActivePipeline();
    console.log('Active Pipeline:', activePipeline);

    // Invia la pipeline al backend con il nome della pipeline
    try {
      const response = await api.post(`/api/project/${progressive_id.progressive_id}/pipeline`, {
        body: JSON.stringify({ 
          pipeline: activePipeline,
          name: pipelineName // Aggiungi il nome della pipeline
        }),
      });

      if (response.status !== 200) {
        const errorData = await response.json();
        throw new Error(`Network response was not ok: ${errorData.message}`);
      }

      const result = response.data;
      console.log('Pipeline saved successfully:', result);
    } catch (error) {
      console.error('Error saving pipeline:', error.message);
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* Pannello laterale per i nodi draggabili */}
      <Box style={sidebarStyles}>
        {/* Campo del nome della pipeline in alto */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Pipeline Name</Typography>
          <TextField
            fullWidth
            label="Enter pipeline name"
            variant="outlined"
            value={pipelineName}
            onChange={(e) => setPipelineName(e.target.value)}
            sx={{ mb: 2 }}
          />
        </Box>

        <Typography variant="h6">Nodes</Typography>
        {availableNodes.map((node) => (
          <Button
            key={node.id}
            variant="outlined"
            onDragStart={(event) => onDragStart(event, node.name)}
            draggable
            sx={{ mt: 1 }}
          >
            {node.name}
          </Button>
        ))}

        <Button
          variant="contained"
          color="primary"
          onClick={handleRunPipeline}
          sx={{ mt: 2 }}
        >
          Run Pipeline
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSavePipeline}
          sx={{ mt: 2 }}
        >
          Save Pipeline
        </Button>
      </Box>

      {/* Area del diagramma */}
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

      {/* Pannello laterale per i parametri del nodo */}
      <NodeSidebar selectedNode={selectedNode} onSave={handleSaveParameters} metabolomicsExperiments={metabolomicsExperiments}/>  

    </Box>
  );
}

// Wrappa DiagramDragDrop in ReactFlowProvider e esporta il componente
export default function App() {
  return (
    <ReactFlowProvider>
      <DiagramDragDrop />
    </ReactFlowProvider>
  );
}