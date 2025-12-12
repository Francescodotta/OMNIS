// src/components/PipelineDashboard.jsx
import React, { useEffect, useState } from "react";
import { useParams } from 'react-router-dom';
import PipelineItemFCS from "../pipelines/PipelineItemFCS";
import { fetchPipelines } from "../../services/fcs_api";
import { Box, Typography, CircularProgress, Alert, Container, Toolbar } from '@mui/material';
import Navbar from "../Navbar";

const PipelineRunDashboard = ({ fetcher = fetchPipelines }) => {
    const { progressive_id } = useParams();
    const [pipelines, setPipelines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getPipelines = async () => {
            try {
                const data = await fetcher(progressive_id);
                setPipelines(data);
            } catch (err) {
                setError("Failed to load pipelines.");
            } finally {
                setLoading(false);
            }
        };
        getPipelines();
    }, [progressive_id, fetcher]);

    return (
        <>
            <Navbar />
            <Toolbar /> {/* spacer to align content with AppBar height */}
            <Container maxWidth="lg" sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
                    <Typography variant="h4" component="h1" align="center" gutterBottom>
                        Running Pipelines
                    </Typography>
                </Box>

                {/* Main area: center content and use responsive grid that adapts to width/height */}
                <Box
                  sx={{
                    minHeight: '60vh', // allow vertical space to expand
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {loading ? (
                    <CircularProgress />
                  ) : error ? (
                    <Alert severity="error">{error}</Alert>
                  ) : pipelines.length > 0 ? (
                    <Box
                      sx={{
                        width: '100%',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                        gap: 2,
                        alignItems: 'stretch',
                        justifyItems: 'center',
                      }}
                    >
                      {pipelines.map((pipeline) => (
                        <Box key={pipeline.progressive_id || pipeline.id || Math.random()} sx={{ width: '100%' }}>
                          <PipelineItemFCS pipeline={pipeline} />
                        </Box>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body1" color="textSecondary" align="center">
                      No running pipelines.
                    </Typography>
                  )}
                </Box>
            </Container>
        </>
    );
};

export default PipelineRunDashboard;