import api from '../../utils/ApiMetabolomics';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, Box, IconButton } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';

const MetabolomicsMatrixTable = ({ projectId }) => {
  const [matrices, setMatrices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchMatrices = async () => {
      try {
        const response = await api.get(`/api/v1/project/${projectId}/matrix`);
        console.log("Making request to:", api.defaults.baseURL + `/api/v1/project/${projectId}/matrix`);
        const data = Array.isArray(response.data) ? response.data : [];
        setMatrices(data);
      } catch (err) {
        setError(err?.message || 'Failed to load matrices');
        setMatrices([]);
      } finally {
        setLoading(false);
      }
    };
    if (projectId) fetchMatrices();
  }, [projectId]);

  if (loading) return <Typography>Loading matrices...</Typography>;
  if (error) return <Typography>Error: {error}</Typography>;

  const handleDownload = (matrix) => {
    // try to open stored file path in a new tab if available
    const filePath = matrix.metabolomics_experiment_file || matrix.metabolomics_experiment_filename;
    if (filePath) {
      window.open(filePath, '_blank');
    } else {
      // fallback: navigate to project metabolomics matrix page
      navigate(`/project/${projectId}/metabolomics/matrix-upload`);
    }
  };

  return (
    <Box sx={{ mt: 2 }}>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Progressive ID</TableCell>
              <TableCell>Experiment Name</TableCell>
              <TableCell>Filename Hash</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {matrices.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    No metabolomics matrices found for this project
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              matrices.map((m) => (
                <TableRow key={m.progressive_id || m.experiment_name || Math.random()}>
                  <TableCell>{m.progressive_id}</TableCell>
                  <TableCell>{m.experiment_name || m.experiment_name_hash}</TableCell>
                  <TableCell>{m.experiment_filename || '-'}</TableCell>
                  <TableCell>
                    <IconButton onClick={() => handleDownload(m)} size="small" title="Open / Download">
                      <DownloadIcon />
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

export default MetabolomicsMatrixTable;