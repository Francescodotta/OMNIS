// import the necessary package for the analysis
import React, {useCallback, useContext, useEffect, useState} from "react";
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

import api from "../../utils/ApiMetabolomics";
import { useParams } from 'react-router-dom';
import { Box, Typography, Paper, Button, TextField, Alert, CircularProgress, List, ListItem, ListItemText, keyframes } from '@mui/material';
import NodeSidebarMetabolomics from "./sidebar/NodeSideBarMetabo";
import ParameterSidebar from "./sidebar/ParameterSidebarMetabo";
import Navbar from "../Navbar";
import { active } from "d3";
import { fetchMetabolomicsMatrices } from "../../services/metabolomics_api";


const initialNodes = [
    {
      id: '1',
      type: 'select_mzML_files',
      data: {
        name: 'select_mzML_files', // Aggiungi questa linea!
        label: 'Select mzML Files',
        parameters: [{ name: 'file_paths', label: 'mzML Files', type: 'files' }],
      },
      position: { x: 250, y: 0 },
    },
];


const initialEdges = [
]


// define the style for the side bar
const sidebarStyles = {
    display: 'flex',
    flexDirection: 'column',
    padding: '10px',
    width: '250px',
    backgroundColor: '#e0e0e0',
    borderRight: '1px solid #ddd',
  };

  
// node to be used in the dragging process
const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/react-flow', nodeType);
    event.dataTransfer.effectAllowed = 'move'
};


// define the function for the metabolomics pipeline processing
function MetabolomicsPipeline() {
    // define the nodes
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    // define the edges as the initial edges
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    // define the available nodes and the method to modify them
    const [availableNodes, setAvailableNodes] = useState([]);
    // define the selected node and the method to modify the variable
    const[selectedNode, setSelectedNode] = useState(null)
    // define the project through react-flow
    const {project} = useReactFlow();
    // define the id of the project
    const progressive_id = useParams();
    //define the state for the name of the pipeline
    const [pipelineName, setPipelineName] = useState([]);
    // set states for handling the metabolomics file
    const [mzMLFiles, setMzMLFiles] = useState([])
    // set state for the matrices
    const [matrices, setMatrices] = useState([]); // Stato per le matrici

    // useEffect to handle the selection of the mzML files by the users
    useEffect(()=>{
        // async function to fetch the mzml files 
        const fetchMzMLFiles = async () => {
            // log the progressive id of the files
            try{
                // get request to the backend to process the metabolomics files 
                const response = await api.get(`/api/project/${progressive_id.progressive_id}/metabolomics`);
                // set the mzML files 
                setMzMLFiles(response.data)

            }catch(error){
                // log the error --> to be displayed in the frontend in the future
                console.error(error)
            }
        };
        fetchMzMLFiles();
    }, [progressive_id.progressive_id]);
    console.log("Available mzML files:", mzMLFiles);


    // useEffect to fetch the available matrices
    useEffect(() => {
        // Function to retrieve available matrices
        const fetchMatrices = async () => {
            try {
                const response = await fetchMetabolomicsMatrices(progressive_id.progressive_id);
                setMatrices(response); // Save matrices to state
            } catch (error) {
                console.error("Error fetching matrices:", error);
            }
        };

        fetchMatrices();
    }, [progressive_id.progressive_id]);

    useEffect(() => {
        // Load JSON functions to process 
        fetch('/forms/processing_functions.json')
          .then((response) => response.json())
          .then((data) => {
            const metabolomicsNodes = data.functions.filter((node) => node.field === 'Metabolomics');
            setAvailableNodes(metabolomicsNodes);
          })
          .catch((error) => console.error('Error loading nodes:', error));
      }, []);

    // handle node connections 
    const onConnect = useCallback(
        (params) => setEdges((eds) => addEdge(params, eds)),
        [setEdges]
    );
      
    // onDragStart node 
    const onDragStart = (event, nodeType) => {
        event.dataTransfer.setData('application/reactflow', nodeType);
        event.dataTransfer.effectAllowed = 'move';
    };

    // drop of the node into the panel
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
              name: nodeType,
              label: nodeData ? nodeData.label : `${nodeType} Node`,  // 🦍 Usa label da nodeData
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

    // deletion logic 
    const onNodesDelete = useCallback(
        (deleted) => {
            const filteredNodes = deleted.filter((node) => node.id != '1');
            if (filteredNodes.length !== deleted.length){
                window.alert("The file selection node cannot be removed");
            }

            setEdges(
                filteredNodes.reduce((acc,node) => {
                    const incomers = getIncomers(node, nodes, edges);
                    const outgoers = getOutgoers(node, nodes, edges);
                    const connectedEdges = getConnectedEdges([node], edges);

                    // remaining edges
                    const remainingEdges = acc.filter(
                        (edge) => !connectedEdges.includes(edges)
                    );

                    const createdEdges = incomers.flatMap(({id : source})=> 
                        outgoers.map(({id: target})=> ({
                            id: `${source}->${target}`,
                            source,
                            target,
                        }))
                    );

                    return[...remainingEdges, ...createdEdges];
                }, edges)
            );
            setNodes((nds) => nds.filter((node) => !filteredNodes.includes(node)));
        },
        [nodes, edges, setEdges, setNodes]
    );


    // function to retrieve the active pipeline
    const getActivePipeline = () => {
        // nodeMap and edgeMap
        const nodeMap = new Map(nodes.map((node) => [node.id, node]));
        const edgeMap = new Map(edges.map((edge)=> [edge.source, edge.target]))

        // empty list for the pipeline
        const pipeline = [];
        // define the current node
        let currentNode = nodeMap.get('1');
        let nodeIndex = 1;

        // while loop over all the nodes present in the analyses 
        while(currentNode) {
            // filter node parameters to keep only the keys that are not numeric
            const filteredParameters = Object.entries(currentNode.data.parameters || {}).reduce(
                (acc, [key, value]) => {
                  if (!isNaN(key)) {
                    return acc;
                  }
                  return { ...acc, [key]: value };
                },
                {}
              );
              pipeline.push({
                ...currentNode, 
                index: nodeIndex,
                data: {...currentNode.data, parameters: filteredParameters},
              });
              const nextNodeId = edgeMap.get(currentNode.id);
              currentNode = nodeMap.get(nextNodeId);
              nodeIndex++;
        }

        return pipeline;
    };

    // function to handle "Run Pipeline" button
    const handleRunPipeline = async () => {
        if (!pipelineName) {
            alert('Please enter a name for the pipeline');
            return;
        }

        const activePipeline = getActivePipeline();
        
        // send the pipeline to the backend for the processes
        try {
            console.log(activePipeline)
            const response = await api.post(
                `/api/project/${progressive_id.progressive_id}/process_pipeline`,
                {
                    body: JSON.stringify({pipeline: activePipeline, name : pipelineName}),
                }
            );

            if (response.status!== 200) {
                const errorData = await response.json();
                throw new Error('Network response was not ok: ', errorData.message)
            }

            const result = response.data;
            console.log("Pipeline saved succesfully", result);
        } catch (error) {
            console.error("Error in running the pipeline: ", error.message);
        }
    };


    return (
        <>
        <Navbar />
        <Box sx={{ display: 'flex', height: '90vh' }}>
            <NodeSidebarMetabolomics
                onDragStart={onDragStart}
                handleRunPipeline={handleRunPipeline}
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
                onNodesDelete={onNodesDelete} // Add the onNodesDelete handler
                style={{ background: '#f0f0f0', borderRadius: '8px' }}
                >
                <Controls />
                </ReactFlow>
            </Box>
            <ParameterSidebar
              selectedNode={selectedNode}
              onSave={handleSaveParameters}
              mzMLFiles={mzMLFiles} // Pass fcsFiles as a prop
              matrices={matrices} // Pass the matrices as a prop
            />
            </Box>
            </>
      );



}






// Wrappa FCPipeline in ReactFlowProvider e esporta il componente
export default function App() {
    return (
      <ReactFlowProvider>
        <MetabolomicsPipeline />
      </ReactFlowProvider>
    );
  }
