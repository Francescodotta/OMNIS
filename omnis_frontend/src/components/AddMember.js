import React, { useState, useEffect } from 'react';
import { Box, TextField, Select, MenuItem, Button, FormControl, InputLabel } from '@mui/material';
import api from '../utils/Api'; // Assumendo che tu abbia un modulo API per ottenere gli utenti esistenti
import { useParams } from 'react-router-dom';

const AddMember = () => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [role, setRole] = useState('');
  const { progressive_id } = useParams();


  useEffect(() => {
    // Fetch existing users from the API
    const fetchUsers = async () => {
      try {
        const response = await api.get(`/api/project/${progressive_id}/nonmembers`); // Cambia l'endpoint con quello corretto
        setUsers(response.data);
      } catch (error) {
        console.error('Error fetching users:', error);
      }
    };

    fetchUsers();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    // Logica per inviare i dati del form al backend
    try {
        const response = await api.post(`/api/v1/project/${progressive_id}/members`, {
            // Include the data you want to send in the request body
            user_id: selectedUser,
            role: role,
            project_id: progressive_id
        });
        // refresh the page
        window.location.reload();
    } catch (error) {
        console.error('Error sending the API:', error);
    }
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 2,
        padding: 2,
        maxWidth: 400,
        margin: '0 auto',
      }}
    >
      <FormControl fullWidth>
        <InputLabel id="user-select-label">Seleziona Utente</InputLabel>
        <Select
          labelId="user-select-label"
          value={selectedUser}
          onChange={(e) => setSelectedUser(e.target.value)}
          required
        >
          {users.map((user) => (
            <MenuItem key={user.progressive_id} value={user.progressive_id}>
              {user.username}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl fullWidth>
        <InputLabel id="role-select-label">Seleziona Ruolo</InputLabel>
        <Select
          labelId="role-select-label"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          required
        >
          <MenuItem value="PI">PI</MenuItem>
          <MenuItem value="Researcher">Researcher</MenuItem>
          <MenuItem value="Guest">Guest</MenuItem>
        </Select>
      </FormControl>
      <Button type="submit" variant="contained" color="primary">
        Aggiungi Membro
      </Button>
    </Box>
  );
};

export default AddMember;