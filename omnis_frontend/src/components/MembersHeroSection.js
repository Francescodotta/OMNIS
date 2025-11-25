import React from 'react';
import { Box, Typography } from '@mui/material';

const MembersHeroSection = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        marginBottom: '16px',
        width: '100%',
    }}
    >
      <Typography variant="h4" component="h1" sx={{ flexGrow: 1.2, textAlign: 'center' }}>
        Gestione membri
      </Typography>
    </Box>
  );
};

export default MembersHeroSection;