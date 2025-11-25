import React, { useState } from 'react';
import { TextField, Button, Typography, Box } from '@mui/material';
import api from '../utils/Api'; // Assumendo che il modulo api sia in questa posizione

const ChangePwd = ({ onSuccess }) => {
  const [old_password, setOldPassword] = useState('');
  const [new_password, setNewPassword] = useState('');
  const [confirm_password, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (new_password !== confirm_password) {
      setMessage('Le nuove password non coincidono');
      return;
    }

    try {
      const response = await api.post('/api/user/password', {
        "old_password" : old_password,
        "new_password":new_password,
      });

      if (response.status === 200) {
        setMessage('Password cambiata con successo');
        if (onSuccess) {
          onSuccess();
        }
      } else {
        setMessage('Errore nel cambiare la password');
      }
    } catch (error) {
      setMessage('Errore nel cambiare la password');
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Cambia Password
      </Typography>
      <form onSubmit={handleSubmit}>
        <Box sx={{ mb: 2 }}>
          <TextField
            label="Vecchia Password"
            type="password"
            fullWidth
            value={old_password}
            onChange={(e) => setOldPassword(e.target.value)}
            required
          />
        </Box>
        <Box sx={{ mb: 2 }}>
          <TextField
            label="Nuova Password"
            type="password"
            fullWidth
            value={new_password}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
        </Box>
        <Box sx={{ mb: 2 }}>
          <TextField
            label="Conferma Nuova Password"
            type="password"
            fullWidth
            value={confirm_password}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </Box>
        <Button variant="contained" color="primary" type="submit" fullWidth>
          Cambia Password
        </Button>
      </form>
      {message && (
        <Typography variant="body1" color="error" sx={{ mt: 2 }}>
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default ChangePwd;