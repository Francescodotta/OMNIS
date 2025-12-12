// GatingStrategyTable Component

import api from '../../utils/ApiFlowCytometry';
import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, 
  Paper, Typography, Box, IconButton, CircularProgress, Button
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit'; // Import EditIcon
// Removed AddIcon import since we're replacing it
import { deleteGatingStrategy } from '../../services/fcs_api';
import styles from '../../styles/components/gatingStrategyTable.module.css'; // Import CSS Module
import AddIcon from '@mui/icons-material/Add';

const GatingStrategyTable = () => {
    const [gatingStrategies, setGatingStrategies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const { projectId, progressiveId } = useParams();
    
    const fetchGatingStrategies = async () => {
        try {
            const response = await api.get(`/flow_cytometry/api/v1/project/${projectId}/flow_cytometry/${progressiveId}/gating_strategies`);
            setGatingStrategies(response.data.data);
        } catch (error) {
            setError(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchGatingStrategies();
    }, []);

    const handleDelete = async (gatingStrategyId) => {
        try {
            await deleteGatingStrategy(projectId, progressiveId, gatingStrategyId);
            fetchGatingStrategies();
        } catch (error) {
            setError(error);
        }
    };
    
    const handleEdit = (gatingStrategyId) => {
        // Navigate to the edit form with gatingStrategy details
        navigate(`/project/${projectId}/fcs_object/${progressiveId}/gatingStrategy/edit/${gatingStrategyId}`, { state: { gatingStrategyId } });
    };

    return (
        <Box className={styles.container}>
            <Typography variant="h4" className={styles.title}>Gating Strategies</Typography>

            {loading ? (
                <div className={styles.loadingContainer}>
                    <CircularProgress />
                </div>
            ) : error ? (
                <Typography variant="h6" className={styles.errorMessage}>Error loading data. Please try again.</Typography>
            ) : (
                <TableContainer component={Paper} className={styles.tableContainer}>
                    <Table className={styles.table}>
                        {/* Apply the tableHeader class to TableHead */}
                        <TableHead className={styles.tableHeader}>
                            <TableRow>
                                {/* Apply the tableHeaderCell class to each TableCell in the header */}
                                <TableCell className={styles.tableHeaderCell}><strong>Name</strong></TableCell>
                                <TableCell className={styles.tableHeaderCell}><strong>Description</strong></TableCell>
                                <TableCell className={styles.tableHeaderCell}><strong>Actions</strong></TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {gatingStrategies.map((gatingStrategy) => (
                                <TableRow key={gatingStrategy.progressive_id} className={styles.tableRow}>
                                    <TableCell>{gatingStrategy.name}</TableCell>
                                    <TableCell>{gatingStrategy.description}</TableCell>
                                    <TableCell className={styles.actionButtons}>
                                        {/* Eye Icon Button - Primary Color */}
                                        <IconButton 
                                            className={styles.iconButton} 
                                            onClick={() => navigate(`/project/${projectId}/fcs_object/${progressiveId}/gating_strategies/${gatingStrategy.progressive_id}/gating_elements`)}
                                        >
                                            <VisibilityIcon />
                                        </IconButton>

                                        {/* Edit Icon Button - Pencil */}
                                        <IconButton 
                                            className={styles.editButton} 
                                            onClick={() => handleEdit(gatingStrategy.progressive_id)}
                                        >
                                            <EditIcon />
                                        </IconButton>

                                        {/* Delete Icon Button - Red Color */}
                                        <IconButton 
                                            className={`${styles.iconButton} ${styles.deleteButton}`} 
                                            onClick={() => handleDelete(gatingStrategy.progressive_id)}
                                        >
                                            <DeleteIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}
            <Button variant="contained" color="primary" startIcon={<AddIcon />} onClick={() => navigate(`/project/${projectId}/fcs_object/${progressiveId}/gatingStrategy/new`)}>
                Create New Gating Strategy
            </Button>
        </Box>
    );
};

export default GatingStrategyTable;