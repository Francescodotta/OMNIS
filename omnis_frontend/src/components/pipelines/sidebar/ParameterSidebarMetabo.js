import React, { useEffect, useState } from "react";
import { Box, Typography, TextField, Button, FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText,
  Paper,
  Divider,
  Chip,
} from '@mui/material';

const ParameterSidebar = ({ selectedNode, onSave, mzMLFiles, matrices }) => {
  const [parameters, setParameters] = useState({});

  console.log(mzMLFiles)

  useEffect(() => {
    if (selectedNode) {
      setParameters(selectedNode.data.parameters || {});
    }
  }, [selectedNode]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    
    // Special handling for select_mzML_files - store both progressive_id and file_paths
    if (name === 'progressive_id' && selectedNode.data.name === 'select_mzML_files') {
      const selectedFiles = mzMLFiles.filter(f => value.includes(f.progressive_id));
      const filePaths = selectedFiles.map(f => f.metabolomics_mzML_file);
      
      setParameters((prev) => ({
        ...prev,
        progressive_id: value,
        file_paths: filePaths
      }));
      return;
    }
    
    // Special handling for select_raw_matrix - store as progressive_id
    if (name === 'progressive_id' && selectedNode.data.name === 'select_raw_matrix') {
      const selectedMatrices = matrices.filter(m => value.includes(m.progressive_id));
      const matrixFiles = selectedMatrices.map(m => m.matrix_file);

      setParameters((prev) => ({
        ...prev,
        progressive_id: value,  // Usa progressive_id invece di matrix_files
        matrix_files: matrixFiles,
      }));
      return;
    }
    
    // Default handling for other parameters
    setParameters((prev) => ({
      ...prev,
      [name]: Array.isArray(value) ? value : value,
    }));
  };

  const handleSave = () => {
    onSave(selectedNode.id, parameters);
  };

  if (!selectedNode) {
    return (
      <Paper
        elevation={10}
        sx={{
          padding: 3,
          width: 260,
          bgcolor: '#0b1524',
          color: 'common.white',
          display: 'flex',
          flexDirection: 'column',
          height: '90vh',
          borderRadius: 3,
          boxShadow: '0 20px 40px rgba(2,12,26,0.6)',
        }}
      >
        <Typography variant="h6">Seleziona un nodo</Typography>
        <Typography variant="body2" sx={{ mt: 1, color: 'rgba(255,255,255,0.7)' }}>
          Clicca su un nodo per personalizzarne i parametri.
        </Typography>
      </Paper>
    );
  }

  const renderParameters = () => {
    // Handle select_mzML_files node
    if (selectedNode.data.name === 'select_mzML_files') {
      return (
        <FormControl fullWidth margin="normal">
          <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>File mzML</InputLabel>
          <Select
            label="File mzML"
            name="progressive_id"
            multiple
            value={parameters.progressive_id || []}
            onChange={handleChange}
            renderValue={(selected) => {
              const selectedNames = selected.map((id) => {
                const file = mzMLFiles.find((f) => f.progressive_id === id);
                return file ? file.metabolomics_experiment_name : id;
              });
              return selectedNames.join(', ');
            }}
            sx={{
              color: 'common.white',
              bgcolor: 'rgba(255,255,255,0.08)',
              borderRadius: 2,
              '.MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(255,255,255,0.2)',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(255,255,255,0.4)',
              },
            }}
          >
            {Array.isArray(mzMLFiles) && mzMLFiles.length > 0 ? (
              mzMLFiles.map((file) => (
                <MenuItem key={file.progressive_id} value={file.progressive_id}>
                  <Checkbox
                    checked={parameters.progressive_id?.indexOf(file.progressive_id) > -1}
                  />
                  <ListItemText primary={file.metabolomics_experiment_name} />
                </MenuItem>
              ))
            ) : (
              <MenuItem disabled>Nessun file mzML disponibile</MenuItem>
            )}
          </Select>
        </FormControl>
      );
    }

    // Handle select_raw_matrix node
    if (selectedNode.data.name === 'select_raw_matrix') {
      return (
        <FormControl fullWidth margin="normal">
          <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Matrici</InputLabel>
          <Select
            label="Matrici"
            name="progressive_id"
            multiple
            value={parameters.progressive_id || []}
            onChange={handleChange}
            renderValue={(selected) => {
              const selectedNames = selected.map((id) => {
                const matrix = matrices.find((m) => m.progressive_id === id);
                return matrix ? matrix.experiment_name : id;
              });
              return selectedNames.join(', ');
            }}
            sx={{
              color: 'common.white',
              bgcolor: 'rgba(255,255,255,0.08)',
              borderRadius: 2,
              '.MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(255,255,255,0.2)',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(255,255,255,0.4)',
              },
            }}
          >
            {Array.isArray(matrices) && matrices.length > 0 ? (
              matrices.map((matrix) => (
                <MenuItem key={matrix.progressive_id} value={matrix.progressive_id}>
                  <Checkbox
                    checked={parameters.progressive_id?.indexOf(matrix.progressive_id) > -1}
                  />
                  <ListItemText primary={matrix.experiment_name} />
                </MenuItem>
              ))
            ) : (
              <MenuItem disabled>Nessuna matrice disponibile</MenuItem>
            )}
          </Select>
        </FormControl>
      );
    }

    // Default: render text fields for other nodes
    return (
      <Box sx={{ overflowY: 'auto', flexGrow: 1, pr: 1 }}>
        {(selectedNode.data.parameters || []).map((param) => (
          <TextField
            key={param.name}
            label={param.label}
            name={param.name}
            type={param.type || 'text'}
            value={parameters[param.name] || ''}
            onChange={handleChange}
            fullWidth
            margin="normal"
            variant="filled"
            InputProps={{
              sx: { bgcolor: 'rgba(255,255,255,0.08)', color: 'common.white', borderRadius: 2 },
            }}
          />
        ))}
      </Box>
    );
  };

  return (
    <Paper
      elevation={10}
      sx={{
        padding: 3,
        width: 260,
        bgcolor: '#06122a',
        color: 'common.white',
        display: 'flex',
        flexDirection: 'column',
        height: '90vh',
        borderRadius: 3,
        boxShadow: '0 20px 40px rgba(2,12,26,0.6)',
      }}
    >
      <Typography variant="h6" sx={{ mb: 1 }}>
        {selectedNode.data.label || 'Nodo senza nome'}
      </Typography>
      <Chip label={selectedNode.type} size="small" sx={{ mb: 2 }} />
      <Divider sx={{ borderColor: 'rgba(255,255,255,0.2)', mb: 2 }} />
      {renderParameters()}
      <Box sx={{ mt: 'auto' }}>
        <Button
          variant="contained"
          fullWidth
          color="secondary"
          onClick={handleSave}
          sx={{ py: 1.5, borderRadius: 2 }}
        >
          Aggiorna parametri
        </Button>
      </Box>
    </Paper>
  );
};

export default ParameterSidebar;
