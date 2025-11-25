import Navbar from "../components/Navbar";
import React, {useEffect, useState} from "react";
import { useParams, useLocation } from 'react-router-dom';
import {Box, Typography, CircularProgress, Paper} from "@mui/material";
import { fetchGatingData} from "../services/fcs_api";
import FlowCytometryScatterPlot from "../components/plot/FlowCytometryScatterplot";
import GatingElementTree from "../components/dashboards/GatingElementTree";

const GatingFlowCytometry = () => {
    const { projectId, progressiveId, gatingStrategyId } = useParams();
    const [gatingData, setGatingData] = useState([]);
    const [statisticsData, setStatisticsData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedGateId, setSelectedGateId] = useState(null);
    // from the query parameter, get the parentId
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const parentId = queryParams.get('parentId');

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                // if there is a parentId, add it to the query parameter
                const data = await fetchGatingData(
                    projectId, 
                    progressiveId, 
                    gatingStrategyId, 
                    parentId
                );
                setGatingData(data.data);
                setStatisticsData(data.statistics)
            } catch (err) {
                console.error("Error fetching data:", err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [projectId, progressiveId, gatingStrategyId, parentId]);

    const handleGateSelect = (gateId) => {
        setSelectedGateId(gateId);
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
                <Typography variant="h5" color="error">{error}</Typography>
            </Box>
        );
    }   

    return (
        <>
          <Navbar />
          <Box p={2}>
            <Typography variant="h5" gutterBottom>Gate Data</Typography>
            <Paper>
              <Box p={2}>
                <Typography variant="h6" gutterBottom>Gate Data</Typography>
                <FlowCytometryScatterPlot 
                data={gatingData} 
                statistics={statisticsData}
                projectId={projectId} 
                progressiveId={progressiveId} />
                {/* Gating element tree component */}
                <Box mt={4}>
                    <GatingElementTree />
                </Box>
              </Box>
            </Paper>
          </Box>
        </>
      );
    };

export default GatingFlowCytometry;