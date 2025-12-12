import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
} from '@mui/material';

export const renderFcsFilePairSelection = (parameters, handleChange, fcsFiles) => {
  // Filter files that have a control_id (paired files)
  const pairedFiles = Array.isArray(fcsFiles) 
    ? fcsFiles.filter(file => file.control_id !== null && file.control_id !== undefined && file.control_id !== '')
    : [];

  return (
    <FormControl fullWidth margin="normal">
      <InputLabel>FCS File Pairs</InputLabel>
      <Select
        label="FCS File Pairs"
        name="files"
        multiple
        value={parameters.files || []}
        onChange={handleChange}
        renderValue={(selected) => selected.join(', ')}
      >
        {pairedFiles.length > 0 ? (
          pairedFiles.map((file) => (
            <MenuItem key={file.progressive_id} value={file.progressive_id}>
              <Checkbox
                checked={
                  parameters.files?.indexOf(file.progressive_id) > -1
                }
              />
              <ListItemText 
                primary={file.filename}
                secondary={`Control ID: ${file.control_id}`}
              />
            </MenuItem>
          ))
        ) : (
          <MenuItem disabled>No paired FCS files available</MenuItem>
        )}
      </Select>
    </FormControl>
  );
};