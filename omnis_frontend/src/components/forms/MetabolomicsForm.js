import React, { useState } from 'react';
import { Button, TextField, Box, Typography, Container } from '@mui/material';
import { styled } from '@mui/system';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/ApiMetabolomics';  // Assicurati di importare il pacchetto api configurato

const Input = styled('input')({
  display: 'none',
});

const MetabolomicsForm = ({ projectId }) => {
  const [file, setFile] = useState(null);
  const [experimentName, setExperimentName] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleExperimentNameChange = (event) => {
    setExperimentName(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setMessage('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('experimentName', experimentName);

    try {
      console.log("Sending request to API...");
      const response = await api.post(`/api/project/${projectId}/metabolomics`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log("Response received from API:", response);
      setMessage(response.data.message);
      console.log(projectId)
      navigate('/project/' + projectId);
    } catch (error) {
      console.error("Error uploading file:", error);
      setMessage('Error uploading file.');
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Typography component="h1" variant="h5">
          Upload Metabolomics Data
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
          <TextField
            margin="normal"
            fullWidth
            id="experiment-name"
            label="Experiment Name"
            name="experiment-name"
            value={experimentName}
            onChange={handleExperimentNameChange}
          />
          <label htmlFor="file-upload">
            <Input accept=".raw" id="file-upload" type="file" onChange={handleFileChange} />
            <Button variant="contained" component="span">
              Choose File
            </Button>
          </label>
          <TextField
            margin="normal"
            fullWidth
            id="file-name"
            label="Selected File"
            name="file-name"
            value={file ? file.name : ''}
            InputProps={{
              readOnly: true,
            }}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
          >
            Upload
          </Button>
          {message && (
            <Typography variant="body2" color="textSecondary" align="center">
              {message}
            </Typography>
          )}
        </Box>
      </Box>
    </Container>
  );
};

export default MetabolomicsForm;