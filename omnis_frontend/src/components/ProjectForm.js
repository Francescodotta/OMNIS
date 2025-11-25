import React, { useState } from 'react';
import { Box, Button, Container, TextField, Typography, MenuItem, Divider, InputAdornment, Paper } from "@mui/material"
import { Science, Description, Title, Biotech, Balance} from "@mui/icons-material"
import api from '../utils/Api';
import Navbar from './Navbar';

const ProjectForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    field: ''
  });

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      // Logica per inviare i dati del form al backend
      await api.post('/api/project', formData);
      console.log('Progetto creato:', formData);
    } catch (error) {
      console.error('Errore nella creazione del progetto:', error);
    }
  };

  return (
    <Box>
      <Navbar />
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            mt: 4,
            borderRadius: 2,
            background: "linear-gradient(to bottom, #ffffff, #f9f9f9)",
          }}
        >
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            sx={{
              color: "primary.main",
              fontWeight: "bold",
              textAlign: "center",
              mb: 3,
            }}
          >
            Crea un nuovo progetto
          </Typography>

          <form onSubmit={handleSubmit}>
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 500, color: "text.secondary" }}>
                Informazioni di base
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <TextField
                label="Nome del progetto"
                variant="outlined"
                fullWidth
                margin="normal"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Title color="primary" />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 2 }}
              />

              <TextField
                label="Descrizione"
                variant="outlined"
                fullWidth
                margin="normal"
                name="description"
                value={formData.description}
                onChange={handleChange}
                required
                multiline
                rows={4}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start" sx={{ alignSelf: "flex-start", mt: 1.5 }}>
                      <Description color="primary" />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 2 }}
              />
            </Box>

            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 500, color: "text.secondary" }}>
                Dettagli tecnici
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <TextField
                label="Campo del progetto"
                variant="outlined"
                fullWidth
                margin="normal"
                name="field"
                value={formData.field}
                onChange={handleChange}
                select
                required
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Science color="primary" />
                    </InputAdornment>
                  ),
                }}
              >
                <MenuItem value="citofluorimetria">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Biotech fontSize="small" color="primary" />
                    Citofluorimetria
                  </Box>
                </MenuItem>
                <MenuItem value="metabolomica">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Balance fontSize="small" color="secondary" />
                    Metabolomica
                  </Box>
                </MenuItem>
                <MenuItem value="proteomica">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Biotech fontSize="small" color="success" />
                    Proteomica
                  </Box>
                </MenuItem>
              </TextField>
            </Box>

            <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 2,
                  boxShadow: 3,
                  "&:hover": {
                    boxShadow: 6,
                    transform: "translateY(-2px)",
                    transition: "transform 0.3s ease",
                  },
                }}
              >
                Crea Progetto
              </Button>
            </Box>
          </form>
        </Paper>
      </Container>
    </Box>
  );
};

export default ProjectForm;