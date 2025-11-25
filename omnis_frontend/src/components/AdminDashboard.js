import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import api from '../utils/Api';
import Navbar from './Navbar';

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [columns, setColumns] = useState([]);
  const navigate = useNavigate();

  const handleRegisterUserClick = () => {
    navigate('/admin/register-user');
  };

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await api.get('/api/users');
        const usersData = response.data;

        if (usersData.length > 0) {
          const firstUser = usersData[0];
          const columns = Object.keys(firstUser).map((key) => ({
            id: key,
            label: key.charAt(0).toUpperCase() + key.slice(1),
          }));
          setColumns(columns);
        }

        setUsers(usersData);
      } catch (error) {
        console.error('Error fetching users:', error);
      }
    };

    fetchUsers();
  }, []);

  return (
    <>
      <Navbar />
      <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Admin Dashboard
        </Typography>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell key={column.id}>{column.label}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  {columns.map((column) => (
                    <TableCell key={column.id}>{user[column.id]}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Button variant="contained" color="primary" sx={{ mt: 2 }} onClick={handleRegisterUserClick}>
          Registra utente
        </Button>
      </Box>
      </Container>
    </>
  );
};

export default AdminDashboard;