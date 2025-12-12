import React from 'react';
import Navbar from '../../components/Navbar'
import GatingStrategyForm from '../../components/forms/GatingStrategyForm';
import { useParams } from 'react-router-dom';
import { Container } from '@mui/material';

const GatingStrategyFormPage = () => {
    const { projectId, progressiveId } = useParams();


    return (
        <>
            <Navbar />
            <Container maxWidth="md">
                <GatingStrategyForm 
                    flowCytometryId={progressiveId}
                    onSuccess={() => {
                        // Optional: Add success callback if needed
                        console.log('Gating strategy created successfully');
                    }}
                />
            </Container>
        </>
    );
};

export default GatingStrategyFormPage;