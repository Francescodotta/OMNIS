import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  Button,
  Box,
  Typography,
} from '@mui/material';

export const renderFcsFileSelection = (parameters, handleChange, fcsFiles, onSelectAll, selectedGroup) => {
  return (
    <FormControl fullWidth margin="normal">
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <InputLabel sx={{ position: 'static', transform: 'none' }}>FCS Files</InputLabel>
        <Button
          size="small"
          variant="outlined"
          onClick={onSelectAll}
          disabled={!Array.isArray(fcsFiles) || fcsFiles.length === 0}
        >
          Select All
        </Button>
      </Box>
      <Select
        label="FCS Files"
        name="files"
        multiple
        value={parameters.files || []}
        onChange={handleChange}
        renderValue={(selected) => {
          if (!selected.length) return "Nessun file selezionato";
          return selected
            .map(
              (id) =>
                fcsFiles.find((file) => file.progressive_id === id)?.filename ||
                id
            )
            .join(', ');
        }}
        sx={{ minHeight: 56, background: '#fff' }}
      >
        {Array.isArray(fcsFiles) && fcsFiles.length > 0 ? (
          fcsFiles.map((file) => (
            <MenuItem key={file.progressive_id} value={file.progressive_id}>
              <Checkbox
                checked={
                  parameters.files?.indexOf(file.progressive_id) > -1
                }
              />
              <ListItemText
                primary={
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {file.filename}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Group: {file.group} | Panel: {file.panel}
                    </Typography>
                  </Box>
                }
              />
            </MenuItem>
          ))
        ) : (
          <MenuItem disabled>No FCS files available</MenuItem>
        )}
      </Select>
    </FormControl>
  );
};