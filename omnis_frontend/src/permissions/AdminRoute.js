import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';

const AdminRoute = ({ component: Component }) => {
  const { role } = useAuth();
  const isAuthenticated = !!localStorage.getItem('access_token');

  if (!isAuthenticated) {
    return <Navigate to="/" />;
  }

  if (role !== 'admin') {
    return <Navigate to="/" />;
  }

  return <Component />;
};

export default AdminRoute;