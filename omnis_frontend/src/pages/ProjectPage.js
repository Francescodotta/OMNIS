import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import {
  Box,
  Container,
  Button,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
} from "@mui/material"
import EngineeringIcon from "@mui/icons-material/Engineering"
import UploadFileIcon from "@mui/icons-material/UploadFile"
import PlayArrowIcon from "@mui/icons-material/PlayArrow"
import AgricultureIcon from '@mui/icons-material/Agriculture';
import ScienceIcon from "@mui/icons-material/Science"
import BiotechIcon from "@mui/icons-material/Biotech"
import AnalyticsIcon from "@mui/icons-material/Analytics"
import CloudUploadIcon from "@mui/icons-material/CloudUpload"
import Navbar from "../components/Navbar"
import ProjectDetails from "../components/HeroSectionProjects"
import MetabolomicsTable from "../components/dashboards/MetabolomicsTable"
import ProteomicsTable from "../components/dashboards/ProteomicsTable"
import CytometryTable from "../components/dashboards/CytometryTable"
import api from "../utils/Api"
import { useEffect } from "react"

const ProjectPage = () => {
  const navigate = useNavigate()
  const { progressive_id } = useParams()
  const [project_field, setProjectField] = useState("")
  const [loading, setLoading] = useState(true)

  // get project information
  useEffect(() => {
    const fetchProject = async () => {
      try {
        setLoading(true)
        const response = await api.get(`/api/project/${progressive_id}`)
        console.log(response.data)
        setProjectField(response.data.field)
        console.log(response.data.field)
      } catch (error) {
        console.error("Error fetching project:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchProject()
  }, [progressive_id])

  const handleUploadMetabolomicsClick = () => {
    navigate(`/project/${progressive_id}/metabolomics/upload`)
  }

  const handleUploadProteomicsClick = () => {
    navigate(`/project/${progressive_id}/proteomics/upload`)
  }

  const handleUploadCytometryClick = () => {
    navigate(`/project/${progressive_id}/flow_cytometry/upload`)
  }

  const handleUploadCytometryBatchClick = () => {
    navigate(`/project/${progressive_id}/flow_cytometry/upload_batch`)
  }

  const handlePipelineClick = () => {
    navigate(`/project/${progressive_id}/pipelines`)
  }

  const handleClick = () => {
    console.log(project_field)
    let targetPath = `/project/${progressive_id}/diagram/unknown`;
  
    if (project_field === 'metabolomica') {
      targetPath = `/project/${progressive_id}/diagram/metabolomics`;
    } else if (project_field === 'citofluorimetria') {
      targetPath = `/project/${progressive_id}/diagram/flow_cytometry`;
    } else if (project_field === 'proteomica') {
      targetPath = `/project/${progressive_id}/diagram/proteomics`;
    }
  
    navigate(targetPath);
  }

  const handleViewPipelineClick = () => {
    let targetPath = `/project/${progressive_id}/running_pipelines_unknown`;
    if (project_field == 'metabolomica'){
      targetPath = `/project/${progressive_id}/metabolomics/running_pipelines`;
    } else if (project_field == 'citofluorimetria'){
      targetPath=`/project/${progressive_id}/running_pipelines`;
    } else if (project_field=='proteomica'){
      targetPath=`/project/${progressive_id}/proteomics/running_pipelines`;
    }
    navigate(targetPath);
  }

  // Helper function to get field-specific styling with more sober colors
  const getFieldColor = () => {
    if (project_field === "metabolomica") return "#6B46C1" // Muted purple
    if (project_field === "citofluorimetria") return "#1E40AF" // Deeper blue
    if (project_field === "proteomica") return "#059669" // Forest green
    return "#475569" // Slate gray
  }

  const getFieldIcon = () => {
    if (project_field === "metabolomica") return <BiotechIcon />
    if (project_field === "citofluorimetria") return <ScienceIcon />
    if (project_field === "proteomica") return <AgricultureIcon />
    return null
  }

  if (loading) {
    return (
      <Box sx={{ width: "100%", minHeight: "90vh", display: "flex", flexDirection: "column" }}>
        <Navbar />
        <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", flex: 1 }}>
          <CircularProgress />
        </Box>
      </Box>
    )
  }

  return (
    <Box sx={{ width: "100%", minHeight: "90vh", display: "flex", flexDirection: "column", bgcolor: "#FAFAFA" }}>
      <Navbar />

      <Container sx={{ flex: 1, py: 3 }}>
        {/* Project Details Section with Hero */}
        <Paper
          elevation={1}
          sx={{
            mb: 4,
            borderRadius: 3,
            overflow: "hidden",
            border: "1px solid",
            borderColor: "#E2E8F0",
          }}
        >
          <Box
            sx={{
              p: 3,
              bgcolor: getFieldColor() + "08",
              borderBottom: "1px solid",
              borderColor: "#E2E8F0",
            }}
          >
            <Typography
              variant="h5"
              component="h1"
              sx={{
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                color: "#1E293B"
              }}
            >
              {getFieldIcon()}
              <Box component="span" sx={{ ml: getFieldIcon() ? 1 : 0 }}>
                Project Overview
              </Box>
            </Typography>
            {project_field && (
              <Chip
                label={project_field === "metabolomica" ? "Metabolomics" : project_field === "citofluorimetria" ? "Cytometry" : project_field === "proteomica" ? "Proteomics" : "Unknown"}
                size="small"
                sx={{
                  mt: 1.5,
                  bgcolor: getFieldColor() + "15",
                  color: getFieldColor(),
                  fontWeight: 500,
                  fontSize: "0.75rem"
                }}
              />
            )}
          </Box>
          <Box sx={{ p: 0 }}>
            <ProjectDetails />
          </Box>
        </Paper>

        {/* Data Tables Section */}
        <Paper
          elevation={1}
          sx={{
            mb: 4,
            borderRadius: 3,
            overflow: "hidden",
            border: "1px solid #E2E8F0"
          }}
        >
          <Box sx={{ p: 0 }}>
            {project_field === "metabolomica" && <MetabolomicsTable projectId={progressive_id} />}
            {project_field === "citofluorimetria" && <CytometryTable projectId={progressive_id} />}
            {project_field === "proteomica" && <ProteomicsTable projectId={progressive_id} />}
          </Box>
        </Paper>

        {/* Workflow Management Section */}
        <Paper
          elevation={1}
          sx={{
            p: 4,
            borderRadius: 3,
            bgcolor: "#FFFFFF",
            border: "1px solid #E2E8F0"
          }}
        >
          <Typography 
            variant="h6" 
            sx={{ 
              mb: 4, 
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              color: "#1E293B"
            }}
          >
            <AnalyticsIcon sx={{ mr: 1.5, color: "#64748B" }} />
            Workflow Management
          </Typography>

          <Grid container spacing={4}>
            {/* Data Upload Section */}
            {(project_field === "metabolomica" || project_field === "citofluorimetria" || project_field === "proteomica") && (
              <Grid item xs={12} lg={6}>
                <Card 
                  variant="outlined" 
                  sx={{ 
                    height: "100%", 
                    borderRadius: 2,
                    border: "1px solid #E2E8F0",
                    backgroundColor: "#FEFEFE",
                    '&:hover': {
                      borderColor: getFieldColor() + "40",
                      boxShadow: "0 4px 12px rgba(0,0,0,0.05)"
                    },
                    transition: 'all 0.3s ease'
                  }}
                >
                  <CardContent sx={{ p: 4 }}>
                    <Typography
                      variant="h6"
                      sx={{ 
                        mb: 2, 
                        fontWeight: 600, 
                        display: "flex", 
                        alignItems: "center",
                        color: "#1E293B"
                      }}
                    >
                      <CloudUploadIcon sx={{ mr: 1.5, color: getFieldColor() }} />
                      Data Upload
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 3, color: "#64748B", lineHeight: 1.6 }}>
                      Upload and manage your {project_field === "metabolomica" ? "metabolomics" : project_field === "citofluorimetria" ? "flow cytometry" : "proteomics"} data files for analysis.
                    </Typography>
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                      {project_field === "metabolomica" && (
                        <Button
                          variant="contained"
                          size="large"
                          startIcon={<UploadFileIcon />}
                          onClick={handleUploadMetabolomicsClick}
                          sx={{
                            backgroundColor: getFieldColor(),
                            color: "white",
                            fontWeight: 500,
                            py: 1.5,
                            borderRadius: 2,
                            textTransform: "none",
                            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                            '&:hover': {
                              backgroundColor: getFieldColor(),
                              filter: "brightness(0.9)",
                              boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
                            }
                          }}
                        >
                          Upload Metabolomics Data
                        </Button>
                      )}
                      {project_field === "citofluorimetria" && (
                        <>
                          <Button
                            variant="contained"
                            size="large"
                            startIcon={<UploadFileIcon />}
                            onClick={handleUploadCytometryBatchClick}
                            sx={{
                              backgroundColor: getFieldColor(),
                              color: "white",
                              fontWeight: 500,
                              py: 1.5,
                              borderRadius: 2,
                              textTransform: "none",
                              boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                              '&:hover': {
                                backgroundColor: getFieldColor(),
                                filter: "brightness(0.9)",
                                boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
                              }
                            }}
                          >
                            FCS Batch Upload
                          </Button>
                          <Button
                            variant="outlined"
                            size="medium"
                            startIcon={<UploadFileIcon />}
                            onClick={handleUploadCytometryClick}
                            sx={{
                              borderColor: getFieldColor(),
                              color: getFieldColor(),
                              fontWeight: 500,
                              py: 1,
                              borderRadius: 2,
                              textTransform: "none",
                              '&:hover': {
                                borderColor: getFieldColor(),
                                backgroundColor: getFieldColor() + "08"
                              }
                            }}
                          >
                            Single FCS Upload
                          </Button>
                        </>
                      )}
                      {project_field === "proteomica" && (
                        <Button
                          variant="contained"
                          size="large"
                          startIcon={<UploadFileIcon />}
                          onClick={handleUploadProteomicsClick}
                          sx={{
                            backgroundColor: getFieldColor(),
                            color: "white",
                            fontWeight: 500,
                            py: 1.5,
                            borderRadius: 2,
                            textTransform: "none",
                            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                            '&:hover': {
                              backgroundColor: getFieldColor(),
                              filter: "brightness(0.9)",
                              boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
                            }
                          }}
                        >
                          Upload Proteomics Data
                        </Button>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Pipeline Management Section */}
            <Grid item xs={12} lg={6}>
              <Card 
                variant="outlined" 
                sx={{ 
                  height: "100%", 
                  borderRadius: 2,
                  border: "1px solid #E2E8F0",
                  backgroundColor: "#FEFEFE",
                  '&:hover': {
                    borderColor: "#94A3B8",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.05)"
                  },
                  transition: 'all 0.3s ease'
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Typography
                    variant="h6"
                    sx={{ 
                      mb: 2, 
                      fontWeight: 600, 
                      display: "flex", 
                      alignItems: "center",
                      color: "#1E293B"
                    }}
                  >
                    <EngineeringIcon sx={{ mr: 1.5, color: "#64748B" }} />
                    Pipeline Management
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 3, color: "#64748B", lineHeight: 1.6 }}>
                    Create, configure, and monitor your analysis pipelines. Build custom workflows for your data processing needs.
                  </Typography>
                  <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <Button
                      variant="contained"
                      size="large"
                      startIcon={<EngineeringIcon />}
                      onClick={handleClick}
                      sx={{
                        backgroundColor: "#475569",
                        color: "white",
                        fontWeight: 500,
                        py: 1.5,
                        borderRadius: 2,
                        textTransform: "none",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                        '&:hover': {
                          backgroundColor: "#334155",
                          boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
                        }
                      }}
                    >
                      Build Pipeline
                    </Button>
                    <Button
                      variant="outlined"
                      size="medium"
                      startIcon={<PlayArrowIcon />}
                      onClick={handleViewPipelineClick}
                      sx={{
                        borderColor: "#64748B",
                        color: "#64748B",
                        fontWeight: 500,
                        py: 1,
                        borderRadius: 2,
                        textTransform: "none",
                        '&:hover': {
                          borderColor: "#475569",
                          backgroundColor: "#F8FAFC",
                          color: "#475569"
                        }
                      }}
                    >
                      Monitor Pipelines
                    </Button>
                    <Button
                      variant="text"
                      size="medium"
                      startIcon={<AnalyticsIcon />}
                      onClick={handlePipelineClick}
                      sx={{
                        color: "#64748B",
                        fontWeight: 500,
                        py: 1,
                        borderRadius: 2,
                        textTransform: "none",
                        '&:hover': {
                          backgroundColor: "#F1F5F9",
                          color: "#475569"
                        }
                      }}
                    >
                      Manage Pipelines
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  )
}

export default ProjectPage