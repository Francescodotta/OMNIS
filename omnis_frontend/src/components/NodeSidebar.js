import React, {useEffect} from 'react';
import { Box, Typography, TextField, Button, MenuItem, Select, FormControl, InputLabel, Checkbox, ListItemText } from '@mui/material';

const NodeSidebar = ({ selectedNode, onSave, metabolomicsExperiments }) => {
  const [parameters, setParameters] = React.useState({});


  useEffect(() => {
    if (selectedNode) {
      setParameters(selectedNode.data.parameters || {});
    }
  }, [selectedNode]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setParameters((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    onSave(selectedNode.id, parameters);
  };

  if (!selectedNode) {
    return <Typography variant="h6">Select a node to edit parameters</Typography>;
  }

  const renderParameters = () => {
    if (selectedNode.data.label === 'Select files') {
      return (
        <>
          <FormControl fullWidth margin="normal">
            <InputLabel>Files</InputLabel>
            <Select
              label="Files"
              name="files"
              multiple
              value={parameters.files || []}
              onChange={handleChange}
              renderValue={(selected) => selected.join(', ')}
            >
              {metabolomicsExperiments.map((file) => (
                <MenuItem key={file.progressive_id} value={file.progressive_id}>
                  <Checkbox checked={parameters.files?.indexOf(file.progressive_id) > -1} />
                  <ListItemText primary={file.metabolomics_experiment_name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </>
        
      );
    }

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

  return (
    <Box sx={{ padding: 2, width: '300px', backgroundColor: '#f0f0f0', borderLeft: '1px solid #ddd' }}>
      <Typography variant="h6">Edit Node Parameters</Typography>
      {renderParameters()}
      <Button variant="contained" color="primary" onClick={handleSave} sx={{ mt: 2 }}>
        Save
      </Button>
    </Box>
  );
};

export default NodeSidebar;