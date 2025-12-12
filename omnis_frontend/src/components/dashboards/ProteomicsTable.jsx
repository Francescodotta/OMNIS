import api from '../../utils/ApiProteomics';
import React, { useEffect, useState } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, Box, IconButton } from '@mui/material';
import EngineeringIcon from '@mui/icons-material/Engineering';

 
const ProteomicsTable = (projectId) => {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();


  useEffect(() => {
    const fetchExperiments = async () => {
      try {
        const response = await api.get(`/api/v1/project/${projectId.projectId}/proteomics_experiment`);
        // Ensure we always set an array
        const experimentsData = Array.isArray(response.data) ? response.data : [];
        setExperiments(experimentsData);
      } catch (err) {
        setError(err.message);
        setExperiments([]); // Set empty array on error
      } finally {
        setLoading(false);
      }
    };

    fetchExperiments();
  }, [projectId]);

  if (loading) {
    return <Typography>Loading...</Typography>;
  }

  if (error) {
    return <Typography>Error: {error}</Typography>;
  }

  const handleNavigate = () =>{
    navigate(`/project/${projectId.projectId}/diagram/proteomics`);
  }

  return (
    <Box sx={{ mt: 4 }}>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Experiment Name</TableCell>
              <TableCell>Project ID</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {experiments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    No proteomics experiments found for this project
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              experiments.map((experiment) => (
                <TableRow key={experiment.progressive_id}>
                  <TableCell>{experiment.progressive_id}</TableCell>
                  <TableCell>{experiment.proteomics_experiment_name}</TableCell>
                  <TableCell>{experiment.project_id}</TableCell>
                  <TableCell>
                    <IconButton onClick={handleNavigate}>
                      <EngineeringIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ProteomicsTable;