import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Typography, 
  Box, 
  Button, 
  CircularProgress, 
  Chip,
  Stack,
  Divider,
  useTheme,
  alpha 
} from '@mui/material';
import { 
  Settings as SettingsIcon, 
  DataObject as DataObjectIcon,
  Add as AddIcon 
} from '@mui/icons-material';
import AgricultureIcon from '@mui/icons-material/Agriculture';
import ScienceIcon from "@mui/icons-material/Science";
import BiotechIcon from "@mui/icons-material/Biotech";
import api from '../utils/Api';

const ProjectDetails = () => {
  const { progressive_id } = useParams();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const theme = useTheme();

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await api.get(`/api/project/${progressive_id}`);
        setProject(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching project:', error);
        setLoading(false);
      }
    };

    fetchProject();
  }, [progressive_id]);

  const handleManageMembersClick = () => {
    navigate(`/project/${progressive_id}/members`);
  };

  const handleStandardizedFieldsClick = () => {
    navigate(`/project/${progressive_id}/standardized-fields`);
  };

  // Helper functions with matching sober colors from ProjectPage
  const getFieldColor = () => {
    if (project?.field === "metabolomica") return "#6B46C1" // Muted purple (same as ProjectPage)
    if (project?.field === "citofluorimetria") return "#1E40AF" // Deeper blue (same as ProjectPage)
    if (project?.field === "proteomica") return "#059669" // Forest green (same as ProjectPage)
    return "#475569" // Slate gray (same as ProjectPage)
  }

  const getFieldIcon = () => {
    if (project?.field === "metabolomica") return <BiotechIcon />
    if (project?.field === "citofluorimetria") return <ScienceIcon />
    if (project?.field === "proteomica") return <AgricultureIcon />
    return null
  }

  const getFieldGradient = () => {
    const fieldColor = getFieldColor();
    return `linear-gradient(135deg, ${fieldColor} 0%, ${alpha(fieldColor, 0.85)} 100%)`
  }

  const getFieldDisplayName = () => {
    if (project?.field === "metabolomica") return "Metabolomics"
    if (project?.field === "citofluorimetria") return "Cytometry"
    if (project?.field === "proteomica") return "Proteomics"
    return project?.field || "Unknown"
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (!project) {
    return (
      <Box sx={{ textAlign: 'center', p: 4 }}>
        <Typography variant="h6" color="error">
          Errore nel caricamento del progetto.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 0 }}>
      {/* Hero Section with sober field-based gradient */}
      <Box
        sx={{
          background: getFieldGradient(),
          color: 'white',
          p: 4,
          borderRadius: '12px 12px 0 0',
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <Typography 
            variant="h3" 
            gutterBottom 
            fontWeight={600}
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              mb: 2
            }}
          >
            {getFieldIcon()}
            <Box component="span" sx={{ ml: getFieldIcon() ? 1.5 : 0 }}>
              {project.name}
            </Box>
          </Typography>
          
          <Typography variant="h6" gutterBottom sx={{ opacity: 0.9, mb: 3, fontWeight: 400 }}>
            {project.description}
          </Typography>
          
          <Chip 
            label={`Campo: ${getFieldDisplayName()}`}
            sx={{ 
              backgroundColor: 'rgba(255,255,255,0.15)', 
              color: 'white',
              fontWeight: 500,
              fontSize: '0.875rem',
              border: '1px solid rgba(255,255,255,0.25)',
              backdropFilter: 'blur(10px)'
            }}
          />
        </Box>
      </Box>

      {/* Action Buttons Section with sober styling */}
      <Box sx={{ p: 4, bgcolor: "#FFFFFF" }}>
        <Typography 
          variant="h6" 
          gutterBottom 
          sx={{ 
            mb: 4, 
            textAlign: 'center', 
            fontWeight: 600,
            color: "#1E293B"
          }}
        >
          Azioni Rapide
        </Typography>
        
        <Stack 
          direction={{ xs: 'column', sm: 'row' }} 
          spacing={3} 
          sx={{ justifyContent: 'center', alignItems: 'center' }}
        >
          {/* Standardized Fields Button with sober primary styling */}
          <Button
            variant="contained"
            size="large"
            startIcon={<DataObjectIcon />}
            endIcon={<AddIcon />}
            onClick={handleStandardizedFieldsClick}
            sx={{
              background: "#475569",
              color: "white",
              boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
              borderRadius: 2,
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 600,
              textTransform: 'none',
              minWidth: 250,
              transition: 'all 0.3s ease',
              '&:hover': {
                background: "#334155",
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                transform: 'translateY(-1px)',
              },
            }}
          >
            Campi Standardizzati
          </Button>

          <Divider 
            orientation="vertical" 
            flexItem 
            sx={{ 
              display: { xs: 'none', sm: 'block' },
              borderColor: "#E2E8F0"
            }} 
          />

          {/* Manage Members Button with sober outlined styling */}
          <Button
            variant="outlined"
            size="large"
            startIcon={<SettingsIcon />}
            onClick={handleManageMembersClick}
            sx={{
              borderColor: "#64748B",
              color: "#64748B",
              borderRadius: 2,
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 600,
              textTransform: 'none',
              minWidth: 250,
              borderWidth: 1.5,
              transition: 'all 0.3s ease',
              '&:hover': {
                borderColor: "#475569",
                backgroundColor: "#F8FAFC",
                color: "#475569",
                borderWidth: 1.5,
                transform: 'translateY(-1px)',
              },
            }}
          >
            Gestisci Membri
          </Button>
        </Stack>

        {/* Info Section with sober typography */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography 
            variant="body2" 
            sx={{ 
              color: "#64748B",
              maxWidth: 600,
              mx: 'auto',
              lineHeight: 1.6,
              fontSize: "0.875rem"
            }}
          >
            Utilizza i campi standardizzati per definire strutture dati coerenti e riutilizzabili nel tuo progetto
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default ProjectDetails;