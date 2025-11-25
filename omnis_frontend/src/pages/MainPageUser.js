import React from 'react';
import Navbar from '../components/Navbar';
import { Button, Box} from '@mui/material';
import UserProjects from '../components/UserProjects';
import { Link } from 'react-router-dom';

const MainPageUser = () => {
  return (
    <div className="main-page-user" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <div style={{ marginTop: '10px', flex: 1 }}>
        <UserProjects apiUrl="/api/project/user" />
      </div>
    </div>
  );
};

export default MainPageUser;