import React, { useState, useEffect } from 'react';
import { Container, Box, Typography, TextField, Button, MenuItem } from '@mui/material';
import Navbar from './Navbar';
import api from '../utils/Api';

const RegisterUser = () => {
  const [schema, setSchema] = useState(null);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    const fetchSchema = async () => {
      try {
        const response = await fetch('/forms/register_user.json');
        const schema = await response.json();
        setSchema(schema);
      } catch (error) {
        console.error('Errore nel recupero dello schema:', error);
      }
    };

    fetchSchema();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await api.post('/api/register', formData);
      console.log('Utente registrato:', formData);
    } catch (error) {
      console.error('Errore nella registrazione dell\'utente:', error);
    }
  };

  if (!schema) {
    return <div>Caricamento...</div>;
  }

  return (
    <>
      <Navbar />
      <Container maxWidth="sm">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Registra un nuovo utente
        </Typography>
        <Box component="form" onSubmit={handleSubmit}>
          {Object.keys(schema.properties).map((key) => {
            const property = schema.properties[key];
            if (property.enum) {
              return (
                <TextField
                  key={key}
                  select
                  label={property.title}
                  name={key}
                  value={formData[key] || ''}
                  onChange={handleChange}
                  fullWidth
                  margin="normal"
                >
                  {property.enum.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
              );
            }
            return (
              <TextField
                key={key}
                label={property.title}
                name={key}
                value={formData[key] || ''}
                onChange={handleChange}
                fullWidth
                margin="normal"
              />
            );
          })}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Button type="submit" variant="contained" color="primary">
              Registra Utente
            </Button>
          </Box>
        </Box>
      </Box>
      </Container>
    </>
  );
};

export default RegisterUser;