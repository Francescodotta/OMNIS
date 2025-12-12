import api from '../../utils/ApiMetabolomics';
import React, { useEffect, useState } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import { 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, 
  Typography, Box, IconButton, Button, Chip, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Select, MenuItem, FormControl, InputLabel, Grid,
  Snackbar, Alert, Checkbox, Tabs, Tab, FormHelperText, Switch, FormControlLabel,
  Accordion, AccordionSummary, AccordionDetails, Divider
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import EngineeringIcon from '@mui/icons-material/Engineering';
import AssignmentIcon from '@mui/icons-material/Assignment';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

// Import standardized fields API functions - FIXED TYPO
import {
  getProjectStandardizedFields,
  assignStandardizedFields,
  bulkAssignStandardizedFields,
  removeStandardizedField,
  validateFieldAssignment
} from '../../services/starndardized_api';

const MetabolomicsTable = (projectId) => {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const navigate = useNavigate();

  // Standardized fields states
  const [fieldDefinitions, setFieldDefinitions] = useState([]);
  const [assignDialog, setAssignDialog] = useState(false);
  const [bulkDialog, setBulkDialog] = useState(false);
  const [selectedExperiment, setSelectedExperiment] = useState(null);
  const [fieldAssignments, setFieldAssignments] = useState({});
  const [selectedExperiments, setSelectedExperiments] = useState([]);
  const [tabValue, setTabValue] = useState(0);
  
  // Form validation states
  const [fieldErrors, setFieldErrors] = useState({});
  const [isValidating, setIsValidating] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    fetchExperiments();
    fetchFieldDefinitions();
  }, [projectId]);

  const fetchExperiments = async () => {
    try {
      const response = await api.get(`/api/project/${projectId.projectId}/metabolomics`);
      setExperiments(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchFieldDefinitions = async () => {
    try {
      console.log('=== Fetching Field Definitions ===');
      console.log('Project ID:', projectId.projectId);
      
      const response = await getProjectStandardizedFields(projectId.projectId);
      console.log('Field definitions response:', response);
      
      const fields = response.standardized_fields || [];
      console.log('Parsed fields:', fields);
      console.log('Number of fields:', fields.length);
      
      // Log each field for debugging
      fields.forEach((field, index) => {
        console.log(`Field ${index}:`, {
          progressive_id: field.progressive_id,
          name: field.field_name,
          display_name: field.field_display_name,
          type: field.data_type,
          values: field.field_values,
          required: field.is_required,
          field_type: field.field_type
        });
      });
      
      setFieldDefinitions(fields);
      
      if (fields.length === 0) {
        console.warn('No field definitions found for project');
        console.log('Project may not have any standardized fields configured yet');
        setFieldDefinitions([]);
      }
    } catch (err) {
      console.error('Error fetching field definitions:', err);
      console.error('Error response:', err.response?.data);
      console.error('Error status:', err.response?.status);
      
      // Show error to user
      setError('Failed to load field definitions: ' + (err.message || 'Unknown error'));
      setFieldDefinitions([]);
    }
  };

  // ===== MISSING HANDLER FUNCTIONS =====

  const handleFieldChange = (fieldName, value) => {
    console.log(`Field change: ${fieldName} = ${value}`);
    
    setFieldAssignments(prev => ({
      ...prev,
      [fieldName]: value
    }));

    // Clear any existing error for this field
    if (fieldErrors[fieldName]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }

    // Real-time validation
    const fieldDef = fieldDefinitions.find(f => f.field_name === fieldName);
    if (fieldDef) {
      validateSingleField(fieldDef, value);
    }
  };

  const validateSingleField = (fieldDef, value) => {
    const errors = {};
    
    // Required field validation
    if (fieldDef.is_required && (!value || value.toString().trim() === '')) {
      errors[fieldDef.field_name] = 'This field is required';
    }
    
    // Data type validation
    if (value && fieldDef.data_type === 'number' && isNaN(value)) {
      errors[fieldDef.field_name] = 'Must be a valid number';
    }
    
    // Select field validation
    if (value && fieldDef.data_type === 'select' && fieldDef.field_values && 
        !fieldDef.field_values.includes(value)) {
      errors[fieldDef.field_name] = 'Must select a valid option';
    }
    
    // Validation rules
    if (value && fieldDef.validation_rules) {
      const rules = fieldDef.validation_rules;
      if (rules.min_value !== undefined && Number(value) < rules.min_value) {
        errors[fieldDef.field_name] = `Must be at least ${rules.min_value}`;
      }
      if (rules.max_value !== undefined && Number(value) > rules.max_value) {
        errors[fieldDef.field_name] = `Must be at most ${rules.max_value}`;
      }
      if (rules.pattern && !new RegExp(rules.pattern).test(value)) {
        errors[fieldDef.field_name] = 'Invalid format';
      }
    }

    setFieldErrors(prev => ({
      ...prev,
      ...errors
    }));
  };

  const handleAssignFields = async () => {
    if (!selectedExperiment) return;

    console.log('=== Assigning Fields ===');
    console.log('Experiment:', selectedExperiment.progressive_id);
    console.log('Field assignments:', fieldAssignments);
    
    setIsValidating(true);
    
    try {
      // Validate all fields before assignment
      const errors = {};
      fieldDefinitions.forEach(fieldDef => {
        const value = fieldAssignments[fieldDef.field_name];
        if (fieldDef.is_required && (!value || value.toString().trim() === '')) {
          errors[fieldDef.field_name] = 'This field is required';
        }
      });

      if (Object.keys(errors).length > 0) {
        setFieldErrors(errors);
        setIsValidating(false);
        return;
      }

      // Filter out empty values
      const filteredAssignments = Object.entries(fieldAssignments)
        .filter(([key, value]) => value !== null && value !== undefined && value !== '')
        .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});

      console.log('Filtered assignments:', filteredAssignments);

      const response = await assignStandardizedFields(
        projectId.projectId,
        selectedExperiment.progressive_id,
        filteredAssignments
      );

      console.log('Assignment response:', response);

      // Update the experiment in the local state
      setExperiments(prev => prev.map(exp => 
        exp.progressive_id === selectedExperiment.progressive_id
          ? { ...exp, standardized_fields: filteredAssignments }
          : exp
      ));

      setSuccessMessage('Fields assigned successfully!');
      setAssignDialog(false);
      setFieldAssignments({});
      setFieldErrors({});
      
    } catch (err) {
      console.error('Error assigning fields:', err);
      setError('Failed to assign fields: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsValidating(false);
    }
  };

  const handleBulkAssign = async () => {
    if (selectedExperiments.length === 0) return;

    console.log('=== Bulk Assigning Fields ===');
    console.log('Selected experiments:', selectedExperiments);
    console.log('Field assignments:', fieldAssignments);
    
    setIsValidating(true);
    
    try {
      // Validate all fields before assignment
      const errors = {};
      fieldDefinitions.forEach(fieldDef => {
        const value = fieldAssignments[fieldDef.field_name];
        if (fieldDef.is_required && (!value || value.toString().trim() === '')) {
          errors[fieldDef.field_name] = 'This field is required';
        }
      });

      if (Object.keys(errors).length > 0) {
        setFieldErrors(errors);
        setIsValidating(false);
        return;
      }

      // Filter out empty values
      const filteredAssignments = Object.entries(fieldAssignments)
        .filter(([key, value]) => value !== null && value !== undefined && value !== '')
        .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});

      console.log('Filtered assignments for bulk:', filteredAssignments);

      const response = await bulkAssignStandardizedFields(
        projectId.projectId,
        selectedExperiments,
        filteredAssignments
      );

      console.log('Bulk assignment response:', response);

      // Update experiments in local state
      setExperiments(prev => prev.map(exp => 
        selectedExperiments.includes(exp.progressive_id)
          ? { ...exp, standardized_fields: { ...exp.standardized_fields, ...filteredAssignments } }
          : exp
      ));

      setSuccessMessage(`Fields assigned to ${selectedExperiments.length} experiments successfully!`);
      setBulkDialog(false);
      setFieldAssignments({});
      setFieldErrors({});
      setSelectedExperiments([]);
      
    } catch (err) {
      console.error('Error bulk assigning fields:', err);
      setError('Failed to bulk assign fields: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsValidating(false);
    }
  };

  const handleRemoveFieldFromAssignment = (fieldName) => {
    console.log('Removing field from assignment:', fieldName);
    
    setFieldAssignments(prev => {
      const newAssignments = { ...prev };
      delete newAssignments[fieldName];
      return newAssignments;
    });

    // Clear any errors for this field
    setFieldErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[fieldName];
      return newErrors;
    });
  };

  const handleRemoveFieldFromExperiment = async (experiment, fieldName) => {
    console.log('Removing field from experiment:', experiment.progressive_id, fieldName);
    
    try {
      await removeStandardizedField(
        projectId.projectId,
        experiment.progressive_id,
        fieldName
      );

      // Update the experiment in local state
      setExperiments(prev => prev.map(exp => {
        if (exp.progressive_id === experiment.progressive_id) {
          const newFields = { ...exp.standardized_fields };
          delete newFields[fieldName];
          return { ...exp, standardized_fields: newFields };
        }
        return exp;
      }));

      setSuccessMessage(`Field "${fieldName}" removed successfully!`);
      
    } catch (err) {
      console.error('Error removing field:', err);
      setError('Failed to remove field: ' + (err.response?.data?.message || err.message));
    }
  };

  // ===== END MISSING HANDLER FUNCTIONS =====

  const openAssignDialog = (experiment) => {
    console.log('=== Opening Assign Dialog ===');
    console.log('Selected experiment:', experiment);
    console.log('Experiment standardized fields:', experiment.standardized_fields);
    console.log('Available field definitions:', fieldDefinitions);
    
    setSelectedExperiment(experiment);
    setFieldAssignments(experiment.standardized_fields || {});
    setFieldErrors({});
    setShowAdvanced(false);
    setAssignDialog(true);
  };

  const renderFieldInput = (fieldDef, value, onChange, showRemove = false) => {
    const fieldValue = value || '';
    const hasError = fieldErrors[fieldDef.field_name];
    
    console.log(`Rendering field ${fieldDef.field_name}:`, {
      fieldDef,
      value: fieldValue,
      hasError,
      dataType: fieldDef.data_type,
      fieldValues: fieldDef.field_values
    });
    
    if (fieldDef.data_type === 'select' && fieldDef.field_values && fieldDef.field_values.length > 0) {
      return (
        <Box key={fieldDef.field_name}>
          <FormControl fullWidth size="small" error={!!hasError}>
            <InputLabel>{fieldDef.field_display_name || fieldDef.field_name} {fieldDef.is_required && '*'}</InputLabel>
            <Select
              value={fieldValue}
              label={`${fieldDef.field_display_name || fieldDef.field_name} ${fieldDef.is_required ? '*' : ''}`}
              onChange={(e) => {
                console.log(`Select change for ${fieldDef.field_name}:`, e.target.value);
                onChange(fieldDef.field_name, e.target.value);
              }}
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
            {hasError && <FormHelperText error>{hasError}</FormHelperText>}
            {!hasError && fieldDef.field_description && (
              <FormHelperText>{fieldDef.field_description}</FormHelperText>
            )}
          </FormControl>
          {showRemove && fieldValue && (
            <Box sx={{ mt: 1 }}>
              <Button
                size="small"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => handleRemoveFieldFromAssignment(fieldDef.field_name)}
              >
                Remove
              </Button>
            </Box>
          )}
        </Box>
      );
    }

    return (
      <Box key={fieldDef.field_name}>
        <TextField
          fullWidth
          size="small"
          label={`${fieldDef.field_display_name || fieldDef.field_name} ${fieldDef.is_required ? '*' : ''}`}
          value={fieldValue}
          onChange={(e) => {
            console.log(`Text field change for ${fieldDef.field_name}:`, e.target.value);
            onChange(fieldDef.field_name, e.target.value);
          }}
          type={fieldDef.data_type === 'number' ? 'number' : 'text'}
          error={!!hasError}
          helperText={hasError || fieldDef.field_description}
          inputProps={{
            ...(fieldDef.data_type === 'number' && fieldDef.validation_rules && {
              min: fieldDef.validation_rules.min_value,
              max: fieldDef.validation_rules.max_value
            })
          }}
        />
        {showRemove && fieldValue && (
          <Box sx={{ mt: 1 }}>
            <Button
              size="small"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => handleRemoveFieldFromAssignment(fieldDef.field_name)}
            >
              Remove
            </Button>
          </Box>
        )}
      </Box>
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

  // Group fields by type for better organization
  const groupedFields = fieldDefinitions.reduce((acc, field) => {
    const type = field.field_type || 'other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(field);
    return acc;
  }, {});

  const requiredFields = fieldDefinitions.filter(field => field.is_required);
  const optionalFields = fieldDefinitions.filter(field => !field.is_required);

  if (loading) {
    return <Typography>Loading...</Typography>;
  }

  if (error && !experiments.length) {
    return <Typography>Error: {error}</Typography>;
  }

  const handleNavigate = () => {
    navigate(`/project/${projectId.projectId}/diagram/`);
  };

  return (
    <Box sx={{ mt: 4 }}>
      {/* Header with Bulk Actions */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Metabolomics Experiments</Typography>
        <Box>
          {selectedExperiments.length > 0 && (
            <Button
              variant="contained"
              startIcon={<AssignmentIcon />}
              onClick={() => setBulkDialog(true)}
              sx={{ mr: 1 }}
            >
              Bulk Assign Fields ({selectedExperiments.length})
            </Button>
          )}
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
              <TableCell>Project ID</TableCell>
              <TableCell>Standardized Fields</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {experiments.map((experiment) => {
              const hasStandardizedFields = experiment.standardized_fields && Object.keys(experiment.standardized_fields).length > 0;
              
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
                  <TableCell>{experiment.metabolomics_experiment_name}</TableCell>
                  <TableCell>{experiment.project_id}</TableCell>
                  <TableCell>
                    <Box display="flex" flexWrap="wrap" gap={0.5}>
                      {hasStandardizedFields ? (
                        Object.entries(experiment.standardized_fields).slice(0, 3).map(([fieldName, fieldValue]) => {
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
                              onDelete={() => handleRemoveFieldFromExperiment(experiment, fieldName)}
                            />
                          );
                        })
                      ) : (
                        <Typography variant="body2" color="textSecondary">
                          No fields assigned
                        </Typography>
                      )}
                      {hasStandardizedFields && Object.keys(experiment.standardized_fields).length > 3 && (
                        <Chip 
                          label={`+${Object.keys(experiment.standardized_fields).length - 3} more`} 
                          size="small" 
                          variant="outlined" 
                        />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <IconButton 
                      onClick={() => openAssignDialog(experiment)} 
                      size="small" 
                      title="Assign/Edit Fields"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton onClick={handleNavigate} title="Engineering Tools">
                      <EngineeringIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Enhanced Assign/Edit Fields Dialog */}
      <Dialog open={assignDialog} onClose={() => setAssignDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              Assign Standardized Fields - {selectedExperiment?.metabolomics_experiment_name}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={showAdvanced}
                  onChange={(e) => setShowAdvanced(e.target.checked)}
                />
              }
              label="Advanced View"
            />
          </Box>
        </DialogTitle>
        <DialogContent>
          {/* Current Assignments Summary */}
          {selectedExperiment?.standardized_fields && Object.keys(selectedExperiment.standardized_fields).length > 0 && (
            <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Current Assignments:
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {Object.entries(selectedExperiment.standardized_fields).map(([fieldName, fieldValue]) => {
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
                      icon={<CheckCircleIcon style={{ color: 'white' }} />}
                    />
                  );
                })}
              </Box>
            </Box>
          )}

          {showAdvanced ? (
            /* Advanced View - Grouped by field type */
            <Box>
              {Object.entries(groupedFields).map(([fieldType, fields]) => (
                <Accordion key={fieldType} defaultExpanded={fieldType === 'experimental_conditions'}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" sx={{ 
                      color: getFieldColor(fieldType),
                      fontWeight: 'bold'
                    }}>
                      {fieldType.replace(/_/g, ' ').toUpperCase()} ({fields.length} fields)
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      {fields.map((fieldDef) => (
                        <Grid item xs={12} sm={6} key={fieldDef.field_name}>
                          {renderFieldInput(
                            fieldDef,
                            fieldAssignments[fieldDef.field_name],
                            handleFieldChange,
                            true
                          )}
                        </Grid>
                      ))}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          ) : (
            /* Simple View - Required fields first */
            <Box>
              {requiredFields.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom color="error">
                    Required Fields
                  </Typography>
                  <Grid container spacing={2}>
                    {requiredFields.map((fieldDef) => (
                      <Grid item xs={12} sm={6} key={fieldDef.field_name}>
                        {renderFieldInput(
                          fieldDef,
                          fieldAssignments[fieldDef.field_name],
                          handleFieldChange
                        )}
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              {optionalFields.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Optional Fields
                  </Typography>
                  <Grid container spacing={2}>
                    {optionalFields.map((fieldDef) => (
                      <Grid item xs={12} sm={6} key={fieldDef.field_name}>
                        {renderFieldInput(
                          fieldDef,
                          fieldAssignments[fieldDef.field_name],
                          handleFieldChange
                        )}
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}
            </Box>
          )}

          {/* Validation Summary */}
          {Object.keys(fieldErrors).length > 0 && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Please fix the following errors:</Typography>
              <ul>
                {Object.entries(fieldErrors).map(([field, error]) => (
                  <li key={field}><strong>{field}</strong>: {error}</li>
                ))}
              </ul>
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleAssignFields} 
            variant="contained"
            disabled={Object.keys(fieldErrors).length > 0 || isValidating}
          >
            {isValidating ? 'Validating...' : 'Assign Fields'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Enhanced Bulk Assign Dialog */}
      <Dialog open={bulkDialog} onClose={() => setBulkDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Bulk Assign Fields to {selectedExperiments.length} Experiments
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            These fields will be assigned to all {selectedExperiments.length} selected experiments. 
            Existing field values will be overwritten.
          </Alert>
          
          <Grid container spacing={2}>
            {fieldDefinitions.map((fieldDef) => (
              <Grid item xs={12} sm={6} key={fieldDef.field_name}>
                {renderFieldInput(
                  fieldDef,
                  fieldAssignments[fieldDef.field_name],
                  handleFieldChange
                )}
              </Grid>
            ))}
          </Grid>

          {Object.keys(fieldErrors).length > 0 && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Please fix the following errors:</Typography>
              <ul>
                {Object.entries(fieldErrors).map(([field, error]) => (
                  <li key={field}><strong>{field}</strong>: {error}</li>
                ))}
              </ul>
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleBulkAssign} 
            variant="contained"
            disabled={selectedExperiments.length === 0 || Object.keys(fieldErrors).length > 0 || isValidating}
          >
            {isValidating ? 'Validating...' : 'Bulk Assign'}
          </Button>
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

export default MetabolomicsTable;