import React, { useState } from 'react';
import flowCytometryApi from '../../utils/ApiFlowCytometry';
import { TextField, Button, Box, Typography, CircularProgress } from '@mui/material';

const FlowCytometryForm = ({ projectId }) => {
    const [file, setFile] = useState(null);
    const [description, setDescription] = useState('');
    const [workspace, setWorkspace] = useState('');
    const [timepoint, setTimepoint] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);


    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(false);

        const formData = new FormData();
        formData.append('cytofluorimetry_file', file);
        formData.append('description', description);
        formData.append('workspace', workspace);
        formData.append('timepoint', timepoint);

        try {
            const response = await flowCytometryApi.post(
                `/api/project/${projectId}/cytofluorimetry`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                }
            );
            setSuccess(true);
            console.log('Upload success:', response.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Error uploading file');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
                Upload Flow Cytometry File
            </Typography>
            
            <Box sx={{ mb: 2 }}>
                <input
                    type="file"
                    onChange={handleFileChange}
                    required
                    accept=".fcs,.FCS"
                />
            </Box>

            <TextField
                fullWidth
                label="Description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                margin="normal"
                multiline
                rows={2}
            />

            <TextField
                fullWidth
                label="Workspace"
                value={workspace}
                onChange={(e) => setWorkspace(e.target.value)}
                margin="normal"
            />

            <TextField
                fullWidth
                label="Timepoint"
                value={timepoint}
                onChange={(e) => setTimepoint(e.target.value)}
                margin="normal"
            />

            <Button
                type="submit"
                variant="contained"
                disabled={loading}
                sx={{ mt: 2 }}
            >
                {loading ? <CircularProgress size={24} /> : 'Upload'}
            </Button>

            {error && (
                <Typography color="error" sx={{ mt: 2 }}>
                    {error}
                </Typography>
            )}
            
            {success && (
                <Typography color="success.main" sx={{ mt: 2 }}>
                    File uploaded successfully!
                </Typography>
            )}
        </Box>
    );
};

export default FlowCytometryForm;