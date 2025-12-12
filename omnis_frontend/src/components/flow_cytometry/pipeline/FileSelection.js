// omnis_frontend/src/components/pipelines/FileSelection.js

import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  Button,
  Alert,
} from '@mui/material';
import api from '../../../utils/ApiFlowCytometry';
import { useParams } from 'react-router-dom';

const FileSelection = ({ onFilesSelected }) => {
  const [fcsFiles, setFcsFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [message, setMessage] = useState('');
  const { progressive_id } = useParams();

  useEffect(() => {
    // Fetch the list of FCS files for the project
    const fetchFcsFiles = async () => {
      try {
        const response = await api.get(
          `/api/project/${progressive_id}/cytofluorimetry`
        );
        setFcsFiles(response.data.data);
        // check that the response is correct
        console.log(response.data.data);
        // type of the response if array
        console.log(Array.isArray(response.data.data));
      } catch (error) {
        console.error('Error fetching FCS files:', error);
      }
    };

    fetchFcsFiles();
  }, [progressive_id]);

  const handleToggleFile = (file) => {
    const currentIndex = selectedFiles.findIndex(
      (f) => f.progressive_id === file.progressive_id
    );
    const newSelectedFiles = [...selectedFiles];

    if (currentIndex === -1) {
      newSelectedFiles.push(file);
    } else {
      newSelectedFiles.splice(currentIndex, 1);
    }

    setSelectedFiles(newSelectedFiles);
  };

  const handleSelectionSubmit = () => {
    if (selectedFiles.length === 0) {
      setMessage('Please select at least one FCS file.');
      return;
    }

    // Pass the selected files to the parent component
    onFilesSelected(selectedFiles);
    setMessage('Files selected successfully.');
  };

  return (
    <Box sx={{ mt: 2 }}>
      <List>
        {fcsFiles.map((file) => (
          <ListItem
            key={file.progressive_id}
            button
            onClick={() => handleToggleFile(file)}
          >
            <Checkbox
              checked={
                selectedFiles.findIndex(
                  (f) => f.progressive_id === file.progressive_id
                ) !== -1
              }
            />
            <ListItemText primary={file.filename} />
          </ListItem>
        ))}
      </List>
      <Button
        variant="contained"
        color="primary"
        onClick={handleSelectionSubmit}
        sx={{ mt: 2 }}
      >
        Confirm Selection
      </Button>
      {message && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {message}
        </Alert>
      )}
    </Box>
  );
};

export default FileSelection;