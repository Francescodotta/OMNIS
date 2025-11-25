import React from 'react';
import Navbar from '../components/Navbar';
import MembersTable from '../components/MembersTable';
import MembersHeroSection from '../components/MembersHeroSection';
import { Container, Box, Button } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';




const HandleMembers = () => {
    const navigate = useNavigate();
    const { progressive_id } = useParams();

    const handleAddMember = () => {
        navigate(`/add-member/${progressive_id}`);
    }


    return (
        <>
        <Navbar />
        <Container maxWidth="md" sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', mt: 4 }}>
        <MembersHeroSection />
        </Container>
        <Container maxWidth="md" sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', mt: 4 }}>
            <Box
            sx={{
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                flexDirection: 'column',
                padding: '16px',
            }}
            >
                <MembersTable />
            </Box>
            <Box
            sx={{
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                flexDirection: 'column',
                padding: '16px',
                mt: 20,
            }}
            >
                <Button
                variant="contained"
                color="primary"
                sx={{ mt: 4 }}
                onClick={handleAddMember}
                >
                    Aggiungi membro
                </Button>
            </Box>
        </Container>
        </>
    );
}

export default HandleMembers;