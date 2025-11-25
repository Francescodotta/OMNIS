import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../utils/Api';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, CircularProgress, Typography, IconButton } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import { useTheme } from '@mui/material/styles';


const MembersTable = () => {
  const { progressive_id } = useParams();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const theme = useTheme();

  useEffect(() => {
    const fetchMembers = async () => {
      try {
        const response = await api.get(`/api/project/${progressive_id}/membership`);
        setMembers(response.data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchMembers();
  }, [progressive_id]);

  const handleEdit = (memberId) => {
    // Logica per modificare il membro
    console.log(`Modifica membro con ID: ${memberId}`);
  };

  const handleDelete = (memberId) => {
    // Logica per eliminare il membro
    console.log(`Elimina membro con ID: ${memberId}`);
  };

  const getTableHeadStyles = () => ({
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    textAlign: 'center',
  });

  if (loading) return <CircularProgress />;
  if (error) return <Typography color="error">Error: {error.message}</Typography>;

  return (
    <TableContainer component={Paper}>
      <Table>
      <TableHead>
          <TableRow>
            <TableCell sx={getTableHeadStyles()}>Username</TableCell>
            <TableCell sx={getTableHeadStyles()}>Role</TableCell>
            <TableCell sx={getTableHeadStyles()}>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {members.map((member) => (
            <TableRow key={member.progressive_id}>
              <TableCell sx={{textAlign:"center"}}>{member.username}</TableCell>
              <TableCell sx={{textAlign:"center"}}>{member.role}</TableCell>
              <TableCell sx={{textAlign:"center"}}>
                {member.role !== 'PI' && (
                  <>
                    <IconButton onClick={() => handleEdit(member.id)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton onClick={() => handleDelete(member.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </>
                )}
                 {member.role === 'PI' && (
                  <IconButton>
                    <RemoveCircleIcon sx={{ color: 'red' }} />
                  </IconButton>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default MembersTable;