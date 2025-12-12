import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
    Typography, Box, IconButton, Button, Dialog, DialogTitle, DialogContent,
    DialogActions, TextField, Select, MenuItem, FormControl, InputLabel,
    Chip, Snackbar, Alert, Checkbox, FormControlLabel, CircularProgress,
    Accordion, AccordionSummary, AccordionDetails, Grid, Card, CardContent
} from '@mui/material';
import {
    Edit as EditIcon,
    Delete as DeleteIcon,
    Add as AddIcon,
    Assessment as AssessmentIcon,
    Warning as WarningIcon,
    CheckCircle as CheckCircleIcon,
    ExpandMore as ExpandMoreIcon,
    Assignment as AssignmentIcon
} from '@mui/icons-material';

import {
    getExperimentsWithStandardizedFields,
    getProjectStandardizedFields,
    assignStandardizedFields,
    updateSingleStandardizedField,
    removeStandardizedField,
    bulkAssignStandardizedFields,
    getExperimentsMissingRequiredFields,
    validateFieldAssignment,
    getStandardizedFieldsSummary
} from '../../services/standardized_fields_api';

const StandardizedFieldsTable = () => {
    const { projectId } = useParams();
    const [experiments, setExperiments] = useState([]);
    const [fieldDefinitions, setFieldDefinitions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState('');
    
    // Dialog states
    const [assignDialog, setAssignDialog] = useState(false);
    const [editDialog, setEditDialog] = useState(false);
    const [bulkDialog, setBulkDialog] = useState(false);
    const [analyticsDialog, setAnalyticsDialog] = useState(false);
    
    // Form states
    const [selectedExperiment, setSelectedExperiment] = useState(null);
    const [selectedField, setSelectedField] = useState('');
    const [fieldAssignments, setFieldAssignments] = useState({});
    const [selectedExperiments, setSelectedExperiments] = useState([]);
    
    // Analytics states
    const [missingFieldsExperiments, setMissingFieldsExperiments] = useState([]);
    const [fieldsSummary, setFieldsSummary] = useState([]);

    useEffect(() => {
        fetchData();
    }, [projectId]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [experimentsData, fieldsData] = await Promise.all([
                getExperimentsWithStandardizedFields(projectId),
                getProjectStandardizedFields(projectId)
            ]);
            setExperiments(experimentsData.experiments || []);
            setFieldDefinitions(fieldsData.standardized_fields || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAssignFields = async () => {
        try {
            await assignStandardizedFields(projectId, selectedExperiment.progressive_id, fieldAssignments);
            setSuccessMessage('Standardized fields assigned successfully');
            setAssignDialog(false);
            setFieldAssignments({});
            fetchData();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleUpdateField = async (experimentId, fieldName, newValue) => {
        try {
            await updateSingleStandardizedField(projectId, experimentId, fieldName, newValue);
            setSuccessMessage('Field updated successfully');
            fetchData();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleRemoveField = async (experimentId, fieldName) => {
        try {
            await removeStandardizedField(projectId, experimentId, fieldName);
            setSuccessMessage('Field removed successfully');
            fetchData();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleBulkAssign = async () => {
        try {
            const assignments = selectedExperiments.map(expId => ({
                experiment_id: expId,
                field_assignments: fieldAssignments
            }));
            
            await bulkAssignStandardizedFields(projectId, assignments);
            setSuccessMessage(`Bulk assignment completed for ${assignments.length} experiments`);
            setBulkDialog(false);
            setSelectedExperiments([]);
            setFieldAssignments({});
            fetchData();
        } catch (err) {
            setError(err.message);
        }
    };

    const openAssignDialog = (experiment) => {
        setSelectedExperiment(experiment);
        setFieldAssignments(experiment.standardized_fields || {});
        setAssignDialog(true);
    };

    const openBulkDialog = () => {
        setFieldAssignments({});
        setBulkDialog(true);
    };

    const openAnalyticsDialog = async () => {
        try {
            const [missingData, summaryData] = await Promise.all([
                getExperimentsMissingRequiredFields(projectId),
                getStandardizedFieldsSummary(projectId)
            ]);
            setMissingFieldsExperiments(missingData.experiments_missing_required_fields || []);
            setFieldsSummary(summaryData.fields_summary || []);
            setAnalyticsDialog(true);
        } catch (err) {
            setError(err.message);
        }
    };

    const renderFieldInput = (fieldDef, value, onChange) => {
        const fieldValue = value || '';
        
        if (fieldDef.data_type === 'select' && fieldDef.field_values && fieldDef.field_values.length > 0) {
            return (
                <FormControl fullWidth size="small">
                    <InputLabel>{fieldDef.field_display_name}</InputLabel>
                    <Select
                        value={fieldValue}
                        label={fieldDef.field_display_name}
                        onChange={(e) => onChange(fieldDef.field_name, e.target.value)}
                    >
                        <MenuItem value="">
                            <em>None</em>
                        </MenuItem>
                        {fieldDef.field_values.map((option) => (
                            <MenuItem key={option} value={option}>
                                {option}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            );
        }

        return (
            <TextField
                fullWidth
                size="small"
                label={fieldDef.field_display_name}
                value={fieldValue}
                onChange={(e) => onChange(fieldDef.field_name, e.target.value)}
                type={fieldDef.data_type === 'number' ? 'number' : 'text'}
                helperText={fieldDef.field_description}
            />
        );
    };

    const getFieldColor = (fieldType) => {
        const colors = {
            'metabolomics': '#6B46C1',
            'experimental_conditions': '#1E40AF',
            'sample_preparation': '#059669',
            'experimental_design': '#DC2626'
        };
        return colors[fieldType] || '#6B7280';
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ mt: 2 }}>
                {error}
            </Alert>
        );
    }

    return (
        <Box sx={{ mt: 4 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h5" component="h2">
                    Standardized Fields Management
                </Typography>
                <Box>
                    <Button
                        variant="outlined"
                        startIcon={<AssessmentIcon />}
                        onClick={openAnalyticsDialog}
                        sx={{ mr: 1 }}
                    >
                        Analytics
                    </Button>
                    <Button
                        variant="contained"
                        startIcon={<AssignmentIcon />}
                        onClick={openBulkDialog}
                        sx={{ mr: 1 }}
                    >
                        Bulk Assign
                    </Button>
                </Box>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>
                                <Checkbox
                                    checked={selectedExperiments.length === experiments.length && experiments.length > 0}
                                    indeterminate={selectedExperiments.length > 0 && selectedExperiments.length < experiments.length}
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            setSelectedExperiments(experiments.map(exp => exp.progressive_id));
                                        } else {
                                            setSelectedExperiments([]);
                                        }
                                    }}
                                />
                            </TableCell>
                            <TableCell>ID</TableCell>
                            <TableCell>Experiment Name</TableCell>
                            <TableCell>Standardized Fields</TableCell>
                            <TableCell>Compliance</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {experiments.map((experiment) => {
                            const hasStandardizedFields = experiment.standardized_fields && Object.keys(experiment.standardized_fields).length > 0;
                            const requiredFields = fieldDefinitions.filter(field => field.is_required);
                            const missingRequired = requiredFields.filter(field => 
                                !experiment.standardized_fields || !experiment.standardized_fields[field.field_name]
                            );

                            return (
                                <TableRow key={experiment.progressive_id}>
                                    <TableCell>
                                        <Checkbox
                                            checked={selectedExperiments.includes(experiment.progressive_id)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setSelectedExperiments([...selectedExperiments, experiment.progressive_id]);
                                                } else {
                                                    setSelectedExperiments(selectedExperiments.filter(id => id !== experiment.progressive_id));
                                                }
                                            }}
                                        />
                                    </TableCell>
                                    <TableCell>{experiment.progressive_id}</TableCell>
                                    <TableCell>{experiment.experiment_name}</TableCell>
                                    <TableCell>
                                        <Box display="flex" flexWrap="wrap" gap={1}>
                                            {hasStandardizedFields ? (
                                                Object.entries(experiment.standardized_fields).map(([fieldName, fieldValue]) => {
                                                    const fieldDef = fieldDefinitions.find(f => f.field_name === fieldName);
                                                    return (
                                                        <Chip
                                                            key={fieldName}
                                                            label={`${fieldName}: ${fieldValue}`}
                                                            size="small"
                                                            style={{
                                                                backgroundColor: fieldDef ? getFieldColor(fieldDef.field_type) : '#6B7280',
                                                                color: 'white'
                                                            }}
                                                            onDelete={() => handleRemoveField(experiment.progressive_id, fieldName)}
                                                        />
                                                    );
                                                })
                                            ) : (
                                                <Typography variant="body2" color="textSecondary">
                                                    No fields assigned
                                                </Typography>
                                            )}
                                        </Box>
                                    </TableCell>
                                    <TableCell>
                                        {missingRequired.length === 0 ? (
                                            <Chip
                                                icon={<CheckCircleIcon />}
                                                label="Compliant"
                                                color="success"
                                                size="small"
                                            />
                                        ) : (
                                            <Chip
                                                icon={<WarningIcon />}
                                                label={`Missing ${missingRequired.length} required`}
                                                color="warning"
                                                size="small"
                                            />
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <IconButton
                                            onClick={() => openAssignDialog(experiment)}
                                            size="small"
                                            title="Assign/Edit Fields"
                                        >
                                            <EditIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Assign/Edit Fields Dialog */}
            <Dialog open={assignDialog} onClose={() => setAssignDialog(false)} maxWidth="md" fullWidth>
                <DialogTitle>
                    Assign Standardized Fields - {selectedExperiment?.experiment_name}
                </DialogTitle>
                <DialogContent>
                    <Grid container spacing={2} sx={{ mt: 1 }}>
                        {fieldDefinitions.map((fieldDef) => (
                            <Grid item xs={12} sm={6} key={fieldDef.field_name}>
                                {renderFieldInput(
                                    fieldDef,
                                    fieldAssignments[fieldDef.field_name],
                                    (fieldName, value) => {
                                        setFieldAssignments(prev => ({
                                            ...prev,
                                            [fieldName]: value
                                        }));
                                    }
                                )}
                                {fieldDef.is_required && (
                                    <Typography variant="caption" color="error">
                                        * Required
                                    </Typography>
                                )}
                            </Grid>
                        ))}
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setAssignDialog(false)}>Cancel</Button>
                    <Button onClick={handleAssignFields} variant="contained">
                        Assign Fields
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Bulk Assign Dialog */}
            <Dialog open={bulkDialog} onClose={() => setBulkDialog(false)} maxWidth="md" fullWidth>
                <DialogTitle>
                    Bulk Assign Fields to {selectedExperiments.length} Experiments
                </DialogTitle>
                <DialogContent>
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        These fields will be assigned to all selected experiments
                    </Typography>
                    <Grid container spacing={2}>
                        {fieldDefinitions.map((fieldDef) => (
                            <Grid item xs={12} sm={6} key={fieldDef.field_name}>
                                {renderFieldInput(
                                    fieldDef,
                                    fieldAssignments[fieldDef.field_name],
                                    (fieldName, value) => {
                                        setFieldAssignments(prev => ({
                                            ...prev,
                                            [fieldName]: value
                                        }));
                                    }
                                )}
                            </Grid>
                        ))}
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setBulkDialog(false)}>Cancel</Button>
                    <Button 
                        onClick={handleBulkAssign} 
                        variant="contained"
                        disabled={selectedExperiments.length === 0}
                    >
                        Bulk Assign
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Analytics Dialog */}
            <Dialog open={analyticsDialog} onClose={() => setAnalyticsDialog(false)} maxWidth="lg" fullWidth>
                <DialogTitle>Standardized Fields Analytics</DialogTitle>
                <DialogContent>
                    <Box sx={{ mt: 2 }}>
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">
                                    Compliance Report ({missingFieldsExperiments.length} non-compliant experiments)
                                </Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                {missingFieldsExperiments.length > 0 ? (
                                    <TableContainer component={Paper} variant="outlined">
                                        <Table size="small">
                                            <TableHead>
                                                <TableRow>
                                                    <TableCell>Experiment ID</TableCell>
                                                    <TableCell>Experiment Name</TableCell>
                                                    <TableCell>Missing Required Fields</TableCell>
                                                </TableRow>
                                            </TableHead>
                                            <TableBody>
                                                {missingFieldsExperiments.map((exp) => (
                                                    <TableRow key={exp.progressive_id}>
                                                        <TableCell>{exp.progressive_id}</TableCell>
                                                        <TableCell>{exp.experiment_name}</TableCell>
                                                        <TableCell>
                                                            {exp.missing_fields?.map(field => (
                                                                <Chip key={field} label={field} size="small" color="error" sx={{ mr: 0.5 }} />
                                                            ))}
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </TableContainer>
                                ) : (
                                    <Alert severity="success">
                                        All experiments are compliant with required standardized fields!
                                    </Alert>
                                )}
                            </AccordionDetails>
                        </Accordion>

                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">
                                    Fields Usage Summary
                                </Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <Grid container spacing={2}>
                                    {fieldsSummary.map((field) => (
                                        <Grid item xs={12} sm={6} md={4} key={field._id}>
                                            <Card variant="outlined">
                                                <CardContent>
                                                    <Typography variant="h6" gutterBottom>
                                                        {field._id}
                                                    </Typography>
                                                    <Typography variant="body2" color="textSecondary">
                                                        Used in {field.usage_count} experiments
                                                    </Typography>
                                                    <Typography variant="body2" color="textSecondary">
                                                        Unique values: {field.unique_values?.length || 0}
                                                    </Typography>
                                                    <Box sx={{ mt: 1 }}>
                                                        {field.unique_values?.slice(0, 3).map(value => (
                                                            <Chip key={value} label={value} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                                                        ))}
                                                        {field.unique_values?.length > 3 && (
                                                            <Typography variant="caption" color="textSecondary">
                                                                +{field.unique_values.length - 3} more
                                                            </Typography>
                                                        )}
                                                    </Box>
                                                </CardContent>
                                            </Card>
                                        </Grid>
                                    ))}
                                </Grid>
                            </AccordionDetails>
                        </Accordion>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setAnalyticsDialog(false)}>Close</Button>
                </DialogActions>
            </Dialog>

            {/* Success Snackbar */}
            <Snackbar
                open={!!successMessage}
                autoHideDuration={6000}
                onClose={() => setSuccessMessage('')}
            >
                <Alert onClose={() => setSuccessMessage('')} severity="success">
                    {successMessage}
                </Alert>
            </Snackbar>

            {/* Error Snackbar */}
            <Snackbar
                open={!!error}
                autoHideDuration={6000}
                onClose={() => setError('')}
            >
                <Alert onClose={() => setError('')} severity="error">
                    {error}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default StandardizedFieldsTable;