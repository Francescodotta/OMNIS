import React from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import ChangePwd from '../components/ChangePwd';
import { Container, Box } from '@mui/material';

const ChangePasswordPage = () => {
  const navigate = useNavigate();

  const handlePasswordChangeSuccess = () => {
    navigate("/user");
  };

  return (
    <div>
      <Navbar />
      <Container maxWidth="sm">
        <Box sx={{ mt: 4 }}>
          <ChangePwd onSuccess={handlePasswordChangeSuccess} />
        </Box>
      </Container>
    </div>
  );
};

export default ChangePasswordPage;