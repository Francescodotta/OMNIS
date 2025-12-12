import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import { renderFcsFileSelection } from './sidebarFunctions/selectFCSFile';
import { renderFcsFilePairSelection } from './sidebarFunctions/selectFCSFilePairAnalysis';

const NodeParameterPanel = ({ selectedNode, onSave, fcsFiles }) => {
  const [parameters, setParameters] = useState({});
  const [selectedGroup, setSelectedGroup] = useState('');
  console.log('fcsFiles:', fcsFiles);

  useEffect(() => {
    if (selectedNode) {
      setParameters(selectedNode.data.parameters || {});
    }
  }, [selectedNode]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setParameters((prev) => {
      const updated = { ...prev, [name]: value };
      // Salva subito se si tratta della selezione dei files
      if (name === 'files') {
        onSave(selectedNode.id, updated);
      }
      return updated;
    });
  };

  const handleSave = () => {
    onSave(selectedNode.id, parameters);
  };

  const handleGroupChange = (event) => {
    setSelectedGroup(event.target.value);
  };

  // Funzione per selezionare tutti i file filtrati
  const handleSelectAll = () => {
    setParameters((prev) => {
      const current = prev.files || [];
      const toAdd = filteredFcsFiles.map((file) => file.progressive_id);
      // Unisci senza duplicati
      const allIds = Array.from(new Set([...current, ...toAdd]));
      const updated = { ...prev, files: allIds };
      onSave(selectedNode.id, updated);
      return updated;
    });
  };

  // Estrai i valori unici di "group" (minuscolo)
  const groupValues = Array.from(
    new Set(
      (fcsFiles || [])
        .map((file) => file.group)
        .filter((g) => g !== undefined && g !== null)
    )
  );

  // Filtra i file in base al gruppo selezionato
  const filteredFcsFiles = selectedGroup
    ? fcsFiles.filter((file) => file.group === selectedGroup)
    : fcsFiles;

  const renderGenericParameters = () => {
    return (selectedNode.data.parameters || []).map((param) => (
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
    ));
  };

  const renderParameters = () => {
    if (
      selectedNode.id === '1' ||
      selectedNode.type === 'select_fcs_files' ||
      selectedNode.data.label === 'Select FCS Files'
    ) {
      return (
        <>
          {groupValues.length > 0 && (
            <FormControl fullWidth margin="normal">
              <InputLabel>Group</InputLabel>
              <Select
                value={selectedGroup}
                label="Group"
                onChange={handleGroupChange}
              >
                <MenuItem value="">All Groups</MenuItem>
                {groupValues.map((group) => (
                  <MenuItem key={group} value={group}>
                    {group}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          {renderFcsFileSelection(
            parameters,
            handleChange,
            filteredFcsFiles,
            handleSelectAll,
            selectedGroup
          )}
        </>
      );
    }
    if (
      selectedNode.type === 'select_fcs_file_pairwise_analysis'
    ){
      return renderFcsFilePairSelection(parameters, handleChange, fcsFiles)
    }

    return renderGenericParameters();
  };

  if (!selectedNode) {
    return (
      <Box sx={{ padding: 2, width: '300px', backgroundColor: '#f0f0f0' }}>
        <Typography variant="h6">Select a node to edit parameters</Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        padding: 2,
        width: '300px',
        backgroundColor: '#f0f0f0',
        borderLeft: '1px solid #ddd',
      }}
    >
      <Typography variant="h6">Edit Node Parameters</Typography>
      {renderParameters()}
      <Button
        variant="contained"
        color="primary"
        onClick={handleSave}
        sx={{ mt: 2 }}
      >
        Save
      </Button>
    </Box>
  );
};

export default NodeParameterPanel;