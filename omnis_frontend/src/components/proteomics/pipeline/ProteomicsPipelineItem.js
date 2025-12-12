import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
} from '@mui/material';

const ProteomicsPipelineItem = ({ selectedNode, onSave, mzMLFiles, matrices = [] }) => {
  const [parameters, setParameters] = useState({});
  const [selectedMatrixDisplay, setSelectedMatrixDisplay] = useState([]);
  const [selectedMzMLDisplay, setSelectedMzMLDisplay] = useState([]);

  console.log(mzMLFiles, "mzMLFiles in ProteomicsPipelineItem");

  useEffect(() => {
    if (selectedNode) {
      setParameters(selectedNode.data.parameters || {});
      // initialize displays if parameters already contain selections
      const initParams = selectedNode.data.parameters || {};
      if (initParams.matrix_files) {
        const initMatrixNames = (initParams.matrix_files || []).map((id) => {
          const m = matrices.find((mx) => String(mx.progressive_id) === String(id));
          return m ? (m.proteomics_experiment_filename || m.proteomics_experiment_name || `matrix_${m.progressive_id}`) : id;
        });
        setSelectedMatrixDisplay(initMatrixNames);
        console.log('Initial selected matrices:', initMatrixNames);
      }
      if (initParams.files) {
        const initMzmlNames = (initParams.files || []).map((id) => {
          const f = mzMLFiles.find((mf) => String(mf.progressive_id) === String(id));
          return f ? (f.proteomics_experiment_name || f.proteomics_experiment_name_hash || f.proteomics_experiment_file || id) : id;
        });
        setSelectedMzMLDisplay(initMzmlNames);
        console.log('Initial selected mzML files:', initMzmlNames);
      }
    }
  }, [selectedNode, matrices, mzMLFiles]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    const normalized = Array.isArray(value) ? value : [value];

    setParameters((prev) => ({
      ...prev,
      [name]: normalized,
    }));

    if (name === 'matrix_files') {
      const selected = normalized.map((id) => {
        const m = matrices.find((mx) => String(mx.progressive_id) === String(id));
        return m ? (m.proteomics_experiment_filename || m.proteomics_experiment_name || `matrix_${m.progressive_id}`) : id;
      });
      setSelectedMatrixDisplay(selected);
      console.log('Selected matrices:', selected);
    }

    if (name === 'files') {
      const selected = normalized.map((id) => {
        const f = mzMLFiles.find((mf) => String(mf.progressive_id) === String(id));
        return f ? (f.proteomics_experiment_name || f.proteomics_experiment_name_hash || f.proteomics_experiment_file || id) : id;
      });
      setSelectedMzMLDisplay(selected);
      console.log('Selected mzML files:', selected);
    }
  };

  const handleSave = () => {
    onSave(selectedNode.id, parameters);
    // log on save too
    console.log('Saving parameters for node', selectedNode.id, parameters);
  };

  if (!selectedNode) {
    return (
      <Box sx={{
        padding: 2,
        width: '180px',
        backgroundColor: '#f0f0f0',
        borderLeft: '1px solid #ddd',
        display: 'flex',
        flexDirection: 'column',
        height: '90vh',
      }}>
        <Typography variant="h6">Select a node to edit parameters</Typography>
      </Box>
    );
  }

  const renderParameters = () => {
    // support both selecting raw mzML files and selecting processed matrices
    if (
      selectedNode.id === '1' ||
      selectedNode.type === 'select_mzML_files' ||
      selectedNode.data.label === 'Select mzML Files'
    ) {
      return (
        <FormControl fullWidth margin="normal">
          <InputLabel>mzML Files</InputLabel>
          <Select
            label="mzML Files"
            name="files"
            multiple
            value={parameters.files || []}
            onChange={handleChange}
            renderValue={(selected) => selected.join(', ')}
          >
            {Array.isArray(mzMLFiles) && mzMLFiles.length > 0 ? (
              mzMLFiles.map((file) => (
                <MenuItem key={file.progressive_id} value={file.progressive_id}>
                  <Checkbox
                    checked={parameters.files?.indexOf(file.progressive_id) > -1}
                  />
                  <ListItemText primary={file.proteomics_experiment_name || file.proteomics_experiment_name_hash || file.proteomics_experiment_file} />
                </MenuItem>
              ))
            ) : (
              <MenuItem disabled>No mzML files available</MenuItem>
            )}
          </Select>

          {/* mostra i nomi o gli id selezionati */}
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Selezionati: {selectedMzMLDisplay.length > 0 ? selectedMzMLDisplay.join(', ') : 'Nessuno'}
            </Typography>
          </Box>
        </FormControl>
      );
    }

    // support selection of processed matrices
    if (selectedNode.type === 'select_raw_matrix' || selectedNode.data.label === 'Select Matrix') {
      return (
        <FormControl fullWidth margin="normal">
          <InputLabel>Matrices</InputLabel>
          <Select
            label="Matrices"
            name="matrix_files"
            multiple
            value={parameters.matrix_files || []}
            onChange={handleChange}
            renderValue={(selected) => selected.join(', ')}
          >
            {Array.isArray(matrices) && matrices.length > 0 ? (
              matrices.map((m) => (
                <MenuItem key={m.progressive_id} value={m.progressive_id}>
                  <Checkbox checked={parameters.matrix_files?.indexOf(m.progressive_id) > -1} />
                  <ListItemText primary={m.proteomics_experiment_filename || m.proteomics_experiment_name || `matrix_${m.progressive_id}`} />
                </MenuItem>
              ))
            ) : (
              <MenuItem disabled>No matrices available</MenuItem>
            )}
          </Select>

          {/* mostra i nomi o gli id selezionati */}
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Selezionati: {selectedMatrixDisplay.length > 0 ? selectedMatrixDisplay.join(', ') : 'Nessuno'}
            </Typography>
          </Box>
        </FormControl>
      );
    }

    return (
      <Box sx={{ overflowY: 'auto', flexGrow: 0.8, paddingRight: 1 }}>
        {(selectedNode.data.parameters || []).map((param) => (
          <TextField
            key={param.name}
            label={param.label}
            name={param.name}
            type={param.type}
            value={parameters[param.name] || ''}
            onChange={handleChange}
            fullWidth
            margin="normal"
          />
        ))}
      </Box>
    );
  };

  return (
    <Box
      sx={{
        padding: 2,
        width: '180px',
        backgroundColor: '#f0f0f0',
        borderLeft: '1px solid #ddd',
        display: 'flex',
        flexDirection: 'column',
        height: '90vh',
      }}
    >
      <Typography variant="h6" sx={{ mb: 2 }}>Edit Node Parameters</Typography>
      {renderParameters()}
      <Box sx={{ mt: 'auto', pt: 2, width: '100%' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSave}
          fullWidth
          sx={{ height: '48px' }}
        >
          Save
        </Button>
      </Box>
    </Box>
  );
};

export default ProteomicsPipelineItem;
