import React from "react";
import { Box, Typography, Button, TextField } from "@mui/material";

const sidebarStyles = {
    display: "flex",
    flexDirection: "column",
    padding: "10px",
    width: "250px",
    backgroundColor: "#e0e0e0",
    borderRight: "1px solid #ddd",
    };

const NodeSidebarProteomics = ({
    onDragStart, handleRunPipeline, pipelineName, setPipelineName, availableNodes,
}) => {
    return (
        <Box style={sidebarStyles}>
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

            {/* Run Pipeline Button */}
            <Button
                variant="contained"
                color="primary"
                onClick={handleRunPipeline}
                sx={{ mt: 2 }}
            >
                Run Pipeline
            </Button>
        </Box>
    )
}

export default NodeSidebarProteomics;