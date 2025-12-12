import React, { useState, useEffect } from 'react';
import {
    Dialog, DialogTitle, DialogContent, DialogActions, Button,
    Grid, Typography, FormControl, InputLabel, Select, MenuItem,
    TextField, Chip, Box, Alert
} from '@mui/material';
import { getProjectStandardizedFields, assignStandardizedFields } from '../../services/starndardized_api';

const QuickFieldAssignment = ({ open, onClose, experiment, projectId, onSuccess }) => {
    const [fieldDefinitions, setFieldDefinitions] = useState([]);
    const [fieldAssignments, setFieldAssignments] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (open && projectId) {
            fetchFieldDefinitions();
            // Initialize with existing fields
            setFieldAssignments(experiment?.standardized_fields || {});
        }
    }, [open, projectId, experiment]);

    const fetchFieldDefinitions = async () => {
        try {
            const response = await getProjectStandardizedFields(projectId);
            setFieldDefinitions(response.standardized_fields || []);
        } catch (err) {
            setError('Failed to load field definitions');
        }
    };

    const handleAssign = async () => {
        try {
            setLoading(true);
            setError('');
            
            // Filter out empty values
            const cleanedAssignments = Object.fromEntries(
                Object.entries(fieldAssignments).filter(([key, value]) => value !== '' && value !== null && value !== undefined)
            );
            
            await assignStandardizedFields(projectId, experiment.progressive_id, cleanedAssignments);
            onSuccess && onSuccess();
            onClose();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const renderFieldInput = (fieldDef) => {
        const value = fieldAssignments[fieldDef.field_name] || '';
        
        if (fieldDef.data_type === 'select' && fieldDef.field_values && fieldDef.field_values.length > 0) {
            return (
                <FormControl fullWidth size="small" key={fieldDef.field_name}>
                    <InputLabel>{fieldDef.field_display_name}</InputLabel>
                    <Select
                        value={value}
                        label={fieldDef.field_display_name}
                        onChange={(e) => setFieldAssignments(prev => ({
                            ...prev,
                            [fieldDef.field_name]: e.target.value
                        }))}
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
                key={fieldDef.field_name}
                fullWidth
                size="small"
                label={fieldDef.field_display_name}
                value={value}
                onChange={(e) => setFieldAssignments(prev => ({
                    ...prev,
                    [fieldDef.field_name]: e.target.value
                }))}
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

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>
                Quick Field Assignment - {experiment?.experiment_name}
            </DialogTitle>
            <DialogContent>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}
                
                {/* Show current assignments */}
                {experiment?.standardized_fields && Object.keys(experiment.standardized_fields).length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Current Assignments:
                        </Typography>
                        <Box display="flex" flexWrap="wrap" gap={1}>
                            {Object.entries(experiment.standardized_fields).map(([fieldName, fieldValue]) => {
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
                                    />
                                );
                            })}
                        </Box>
                    </Box>
                )}

                <Grid container spacing={2} sx={{ mt: 1 }}>
                    {fieldDefinitions.map((fieldDef) => (
                        <Grid item xs={12} sm={6} key={fieldDef.field_name}>
                            {renderFieldInput(fieldDef)}
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
                <Button onClick={onClose} disabled={loading}>
                    Cancel
                </Button>
                <Button 
                    onClick={handleAssign} 
                    variant="contained" 
                    disabled={loading}
                >
                    {loading ? 'Assigning...' : 'Assign Fields'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default QuickFieldAssignment;