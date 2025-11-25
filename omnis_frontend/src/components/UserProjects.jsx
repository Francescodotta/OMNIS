"use client"

import { useEffect, useState } from "react"
import {
  Card,
  Box,
  CardContent,
  Typography,
  Grid,
  Button,
  Paper,
  Chip,
  IconButton,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Fade,
  Tooltip,
} from "@mui/material"
import DeleteIcon from "@mui/icons-material/Delete"
import FolderIcon from "@mui/icons-material/Folder"
import AddCircleIcon from "@mui/icons-material/AddCircle"
import ArrowForwardIcon from "@mui/icons-material/ArrowForward"
import api from "../utils/Api"
import { useNavigate, Link } from "react-router-dom"

const UserProjects = () => {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await api.get("/api/project/user")
        setProjects(response.data)
      } catch (error) {
        console.error("Error fetching projects:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchProjects()
  }, [])

  const handleDelete = async (projectId) => {
    try {
      console.log("projectId:", projectId)
      await api.delete(`/api/project/${projectId}`)
      const updatedProjects = projects.filter((project) => project.id !== projectId)
      setProjects(updatedProjects)
      setDeleteDialogOpen(false)
    } catch (error) {
      console.error("Error deleting project:", error)
    }
  }

  const handleCardClick = (projectId) => {
    navigate(`/project/${projectId}`)
  }

  const openDeleteDialog = (project) => {
    setProjectToDelete(project)
    setDeleteDialogOpen(true)
  }

  const closeDeleteDialog = () => {
    setDeleteDialogOpen(false)
    setProjectToDelete(null)
  }

  // Helper function to get a color based on the field
  const getFieldColor = (field) => {
    const fieldMap = {
      "Web Development": "#2196f3",
      "Mobile Development": "#4caf50",
      "Data Science": "#9c27b0",
      IoT: "#ff9800",
      AI: "#f44336",
    }

    return fieldMap[field] || "#607d8b"
  }

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: "70vh" }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ mt: 4, px: { xs: 2, md: 4 } }}>
      {/* Header Section */}
      <Paper elevation={0} sx={{ p: 3, mb: 4, borderRadius: 2, bgcolor: "background.paper" }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
          <Box>
            <Typography variant="h4" component="h1" sx={{ fontWeight: "bold" }}>
              My Projects
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
              Manage and explore your current projects
            </Typography>
          </Box>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddCircleIcon />}
            sx={{ mt: { xs: 2, sm: 0 }, borderRadius: 2 }}
            component={Link} 
            to="/create-project"
          >
            Create New Project
          </Button>
        </Box>
      </Paper>

      {/* Projects Grid */}
      {projects.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: "center", borderRadius: 2, border: "1px dashed", borderColor: "divider" }}>
          <FolderIcon sx={{ fontSize: 60, color: "text.secondary", mb: 2 }} />
          <Typography variant="h6">No projects yet</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 3 }}>
            Get started by creating your first project to organize your work.
          </Typography>
          <Button variant="contained" color="primary" startIcon={<AddCircleIcon />} sx={{ borderRadius: 2 }}>
            Create Your First Project
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project) => (
            <Fade in={true} key={project.progressive_id} timeout={500}>
              <Grid item xs={12} sm={6} md={4} lg={3}>
                <Card
                  sx={{
                    height: "100%",
                    borderRadius: 2,
                    transition: "all 0.3s",
                    "&:hover": {
                      boxShadow: 6,
                      transform: "translateY(-4px)",
                    },
                  }}
                >
                  <CardContent sx={{ p: 0, "&:last-child": { pb: 0 } }}>
                    {/* Card Header */}
                    <Box
                      sx={{
                        p: 2,
                        borderBottom: "1px solid",
                        borderColor: "divider",
                        cursor: "pointer",
                        "&:hover": { bgcolor: "action.hover" },
                      }}
                      onClick={() => handleCardClick(project.progressive_id)}
                    >
                      <Typography
                        variant="h6"
                        component="div"
                        sx={{
                          fontWeight: "bold",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        {project.name}
                        <ArrowForwardIcon fontSize="small" color="action" />
                      </Typography>
                      <Chip
                        label={project.field}
                        size="small"
                        sx={{
                          mt: 1,
                          bgcolor: `${getFieldColor(project.field)}20`,
                          color: getFieldColor(project.field),
                          fontWeight: 500,
                        }}
                      />
                    </Box>

                    {/* Card Body */}
                    <Box sx={{ p: 2 }}>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          height: 60,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          display: "-webkit-box",
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: "vertical",
                        }}
                      >
                        {project.description}
                      </Typography>
                    </Box>

                    {/* Card Footer */}
                    <Box
                      sx={{
                        p: 2,
                        pt: 1,
                        display: "flex",
                        justifyContent: "flex-end",
                        borderTop: "1px solid",
                        borderColor: "divider",
                      }}
                    >
                      <Tooltip title="Delete Project">
                        <IconButton color="error" size="small" onClick={() => openDeleteDialog(project)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Fade>
          ))}
        </Grid>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={closeDeleteDialog}>
        <DialogTitle>Delete Project</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{projectToDelete?.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeleteDialog} color="primary">
            Cancel
          </Button>
          <Button onClick={() => handleDelete(projectToDelete?.progressive_id)} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default UserProjects
