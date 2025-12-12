import React, { useCallback, useState, useEffect } from 'react';
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
import { Box } from '@mui/material';
import { useParams } from 'react-router-dom';
import proteomicsApi from '../../../utils/ApiProteomics';
// follow the importing adding the sidebar, node parameter panel
import ProteomicsPipelineItem from './ProteomicsPipelineItem';
import NodeSidebarProteomics from './ProteomicsSidebar';


// setup the initial nodes parameters
const initialNodes = [
    {
        id: '1',
        type: 'select_mzML_files', // must match the check in your sidebar/component
        data: {
            label: 'Select mzML Files', // must match the check in your sidebar/component
            parameters: [
                {
                    name: 'files',
                    label: 'Proteomics files',
                    type: 'text'
                }
            ],
        },
        position: { x: 250, y: 0 },
    }
];

// set the initial edges as an empty array
const initialEdges = [];

// Define the proteomics pipeline function
function ProteomicsPipeline() {
    // define the nodes variable
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const [availableNodes, setAvailableNodes] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const { project } = useReactFlow();
    const progressive_id = useParams(); // progressive id
    const [pipelineName, setPipelineName] = useState('');
    const [rawFiles, setRawFiles] = useState([]); // Define rawFiles state
    const [matrices, setMatrices] = useState([]); // matrices list

    // effect to load nodes from JSON file and filter only proteomics nodes
    useEffect(() => {
        fetch('/forms/processing_functions.json')
            .then((response) => response.json())
            .then((data) => {
                const proteomicsNodes = data.functions.filter(
                    (node) => node.field === 'Proteomics'
                );
                setAvailableNodes(proteomicsNodes);
            })
            .catch((error) => console.error('Error loading nodes:', error));
    }, []);

    // useEffect to fetch the list of raw proteomics files for the project
    useEffect(()=>{
        // async function to fetch the raw files 
        const fetchRawFiles = async () => {
            // log the progressive id of the files
            try{
                // get request to the backend to process the metabolomics files 
                const response = await proteomicsApi.get(`/api/v1/project/${progressive_id.progressive_id}/proteomics_experiment`);
                // set the raw files 
                setRawFiles(response.data);
                console.log("Raw files fetched:", response.data);

            }catch(error){
                // log the error --> to be displayed in the frontend in the future
                console.error(error)
            }
        };
        fetchRawFiles();
    }, [progressive_id.progressive_id]);

    // fetch processed matrices for this project
    useEffect(() => {
        const fetchMatrices = async () => {
            try {
                const res = await proteomicsApi.get(`/api/v1/project/${progressive_id.progressive_id}/matrix`);
                setMatrices(Array.isArray(res.data) ? res.data : []);
            } catch (err) {
                console.error("Error fetching matrices", err);
                setMatrices([]);
            }
        };
        if (progressive_id?.progressive_id) fetchMatrices();
    }, [progressive_id.progressive_id]);

    // logic for the onConnect function, it creates the connection between the nodes
    // and sets the edges state
    // the onConnect function is called when a new edge is created
    const onConnect = useCallback(
        (params) => setEdges((eds) => addEdge(params, eds)),
        [setEdges]
    );

    // logic for the onDragStart function
    // it is called when a node is dragged from the sidebar, it creates a new node and sets the nodes state
    const onDragStart = (event, nodeType) => {
        event.dataTransfer.setData('application/reactflow', nodeType);
        event.dataTransfer.effectAllowed = 'move';
    }

    // logic for the onDrop function
    // it is called when a node is dropped on the canvas, it creates a new node and sets the nodes state
    const onDrop = useCallback(
        (event) => {
            const nodeType = event.dataTransfer.getData('application/reactflow'); // this contains node.name from the sidebar
            const position = project({x: event.clientX, y: event.clientY});
            const nodeData = availableNodes.find((node) => node.name === nodeType);
            // create a new node with the data from the JSON file; use nodeData.name as type
            const newNode = {
                id: (nodes.length + 1).toString(),
                type: nodeData ? nodeData.name : nodeType,
                position,
                data: {
                    label: nodeData?.label || `${nodeType} Node`,
                    parameters: nodeData ? nodeData.parameters : [],
                },
            };
            setNodes((nds) => nds.concat(newNode));
        },
        [nodes, setNodes, availableNodes, project]
    );


    // logic for the onNodeClick function
    const onNodeClick = useCallback((event, node) => {
        setSelectedNode(node);
    }, []);

    // logic for the onDragOver function
    const onDragOver = (event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    };

    // logic for the handleSaveParameters function
    const handleSaveParameters = (nodeId, parameters) => {
        setNodes((nodes) =>
            nodes.map((node)=>
                node.id === nodeId ? {...node, data: {...node.data, parameters}} : node)
        );
    };

    // logic for the onNodesDelete function adding the condition to prevent the deletion of the node with id '1'
    const onNodesDelete = useCallback(
        (deleted) => {
            const filteredNodes = deleted.filter((n) => n.id !== '1');
            if (filteredNodes.length !== deleted.length) {
                alert("The selected node cannot be removed.");
            }

            // Remove nodes from state (use filteredNodes)
            setNodes((nds) => nds.filter((n) => !filteredNodes.includes(n)));

            // Rebuild edges: remove edges connected to deleted nodes and connect incomers -> outgoers
            setEdges(
                filteredNodes.reduce((acc, node) => {
                    // pass current edges to the helpers so they don't operate on undefined
                    const incomers = getIncomers(node, nodes, edges);
                    const outgoers = getOutgoers(node, nodes, edges);
                    const connectedEdges = getConnectedEdges([node], edges);

                    const remainingEdges = acc.filter((edge) => !connectedEdges.includes(edge));

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
         },
         [nodes, edges, setEdges, setNodes]
     );

    // function to get the active pipeline
    const getActivePipeline = () => {
        const nodeMap = new Map(nodes.map((node) => [node.id, node]));
        const edgeMap = new Map(edges.map((edge) => [edge.source, edge.target]));

        // define an empty array to store the pipeline
        const pipeline = [];

        // start from the initial node and traverse the graph
        let currentNode = nodeMap.get('1');
        let nodeIndex = 1;

        while (currentNode) {
            // filter node parameters to keep only keys that are not numeric
            const filteredParameters = Object.entries(currentNode.data.parameters || {}).reduce(
                (acc, [key, value]) => {
                    if (!isNaN(key)) {
                        return acc;
                    }
                    return {...acc, [key]:value}                
                }, {}
            );

            // create a new node object with the filtered parameter
            pipeline.push(
                {
                    ...currentNode,
                    index: nodeIndex, 
                    data: {...currentNode.data, parameters: filteredParameters},
                }
            );
            const nextNodeId = edgeMap.get(currentNode.id);
            currentNode = nodeMap.get(nextNodeId);
            nodeIndex++;

        }
        return pipeline;
    };

    // function to handle the run pipeline button
    const handleRunPipeline = async () => {
        if (!pipelineName){
            alert("Please enter a name for the pipeline.");
            return;
        }

        const activePipeline = getActivePipeline();
        console.log("Active Pipeline:", activePipeline);

        // send the pipeline to the backend
        try {
            const response = await proteomicsApi.post(
                `/api/v1/project/${progressive_id.progressive_id}/pipeline`,
                {
                    body: JSON.stringify({pipeline: activePipeline, name: pipelineName}),
                }
            );

            const result = response.data;
            console.log("Pipeline result:", result);
        }catch (error){
            console.error("Error saving pipeline:", error.message);
            alert("Error saving pipeline: " + error.message);
        }
    };

      return (
        <Box sx={{ display: 'flex', height: '100vh' }}>
          <NodeSidebarProteomics
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
          <ProteomicsPipelineItem
            selectedNode={selectedNode}
            onSave={handleSaveParameters}
            mzMLFiles={rawFiles} // raw mzML experiments
            matrices={matrices} // processed matrices list
          />
        </Box>
      );
    }
    
    // Wrap FCPipeline in ReactFlowP\rovider and export the component
    export default function App() {
      return (
        <ReactFlowProvider>
          <ProteomicsPipeline />
        </ReactFlowProvider>
      );
}
