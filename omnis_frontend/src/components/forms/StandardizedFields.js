import { useState, useEffect } from "react"
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  Tooltip,
  Badge
} from "@mui/material"
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FileCopy as CloneIcon,
  ExpandMore as ExpandMoreIcon,
  ArrowBack as ArrowBackIcon,
  DataObject as DataObjectIcon,
  Settings as SettingsIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon
} from "@mui/icons-material"
import AgricultureIcon from '@mui/icons-material/Agriculture';
import ScienceIcon from "@mui/icons-material/Science"
import BiotechIcon from "@mui/icons-material/Biotech"
import Navbar from "../Navbar";
import api from "../../utils/Api";


const StandardizedFieldsPage = () => {
  const navigate = useNavigate()
  const { projectId } = useParams()
  const [fields, setFields] = useState([])
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingField, setEditingField] = useState(null)
  const [selectedFieldType, setSelectedFieldType] = useState('all')
  const [expandedField, setExpandedField] = useState(null)
  const [notification, setNotification] = useState(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [fieldToDelete, setFieldToDelete] = useState(null)

  // Form state for creating/editing fields
  const [formData, setFormData] = useState({
    field_type: 'condition',
    field_name: '',
    field_description: '',
    field_values: [],
    is_required: false,
    data_type: 'text',
    validation_rules: {}
  })

  const fieldTypes = [
    { value: 'condition', label: 'Condition', icon: '🔬', description: 'Experimental conditions and variables' },
    { value: 'sample_preparation', label: 'Sample Preparation', icon: '🧪', description: 'Sample processing methods' },
    { value: 'treatment', label: 'Treatment', icon: '💊', description: 'Applied treatments and interventions' },
    { value: 'protocol', label: 'Protocol', icon: '📋', description: 'Standardized procedures' },
    { value: 'custom', label: 'Custom', icon: '⚙️', description: 'Project-specific fields' }
  ]

  const dataTypes = [
    { value: 'text', label: 'Text', icon: '📝' },
    { value: 'number', label: 'Number', icon: '🔢' },
    { value: 'select', label: 'Select (dropdown)', icon: '📋' },
    { value: 'boolean', label: 'Boolean (yes/no)', icon: '✅' },
    { value: 'date', label: 'Date', icon: '📅' }
  ]

  // Get field-specific colors (same as ProjectPage)
  const getFieldColor = () => {
    if (project?.field === "metabolomica") return "#6B46C1" // Muted purple
    if (project?.field === "citofluorimetria") return "#1E40AF" // Deeper blue
    if (project?.field === "proteomica") return "#059669" // Forest green
    return "#475569" // Slate gray
  }

  const getFieldIcon = () => {
    if (project?.field === "metabolomica") return <BiotechIcon />
    if (project?.field === "citofluorimetria") return <ScienceIcon />
    if (project?.field === "proteomica") return <AgricultureIcon />
    return null
  }

  const getFieldDisplayName = () => {
    if (project?.field === "metabolomica") return "Metabolomics"
    if (project?.field === "citofluorimetria") return "Cytometry"
    if (project?.field === "proteomica") return "Proteomics"
    return project?.field || "Unknown"
  }

  useEffect(() => {
    if (projectId) {
      fetchProject()
      fetchStandardizedFields()
    }
  }, [projectId, selectedFieldType])

  const fetchProject = async () => {
    try {
      const response = await api.get(`/api/project/${projectId}`)
      setProject(response.data)
    } catch (error) {
      console.error('Error fetching project:', error)
      showNotification('Failed to fetch project details', 'error')
    }
  }

  const fetchStandardizedFields = async () => {
    if (!projectId) {
      showNotification('Project ID is missing', 'error')
      return
    }

    setLoading(true)
    try {
      const url = selectedFieldType === 'all' 
        ? `api/projects/${projectId}/standardized-fields`
        : `api/projects/${projectId}/standardized-fields?field_type=${selectedFieldType}`
      
      const response = await api.get(url)
      setFields(response.data)
    } catch (error) {
      console.error('Error fetching standardized fields:', error)
      showNotification(
        error.response?.data?.error || 'Failed to fetch standardized fields', 
        'error'
      )
    } finally {
      setLoading(false)
    }
  }

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type })
  }

  const resetForm = () => {
    setFormData({
      field_type: 'condition',
      field_name: '',
      field_description: '',
      field_values: [],
      is_required: false,
      data_type: 'text',
      validation_rules: {}
    })
    setEditingField(null)
    setShowCreateForm(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!projectId) {
      showNotification('Project ID is missing', 'error')
      return
    }

    setLoading(true)

    try {
      const url = editingField 
        ? `api/projects/${projectId}/standardized-fields/${editingField.progressive_id}`
        : `api/projects/${projectId}/standardized-fields`
      
      let response
      if (editingField) {
        response = await api.put(url, formData)
      } else {
        response = await api.post(url, formData)
      }

      showNotification(
        editingField ? 'Field updated successfully' : 'Field created successfully',
        'success'
      )
      resetForm()
      fetchStandardizedFields()
    } catch (error) {
      console.error('Error submitting form:', error)
      showNotification(
        error.response?.data?.error || 'Operation failed', 
        'error'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (field) => {
    setFormData({
      field_type: field.field_type,
      field_name: field.field_name,
      field_description: field.field_description || '',
      field_values: field.field_values || [],
      is_required: field.is_required || false,
      data_type: field.data_type,
      validation_rules: field.validation_rules || {}
    })
    setEditingField(field)
    setShowCreateForm(true)
  }

  const handleDelete = async () => {
    if (!projectId || !fieldToDelete) return

    setLoading(true)
    try {
      await api.delete(`api/projects/${projectId}/standardized-fields/${fieldToDelete.progressive_id}`)
      showNotification('Field deleted successfully', 'success')
      fetchStandardizedFields()
      setDeleteDialogOpen(false)
      setFieldToDelete(null)
    } catch (error) {
      console.error('Error deleting field:', error)
      showNotification(
        error.response?.data?.error || 'Failed to delete field', 
        'error'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleClone = async (fieldId) => {
    if (!projectId) {
      showNotification('Project ID is missing', 'error')
      return
    }

    setLoading(true)
    try {
      await api.post(`api/projects/${projectId}/standardized-fields/${fieldId}/clone`, {
        target_project_id: projectId
      })
      showNotification('Field cloned successfully', 'success')
      fetchStandardizedFields()
    } catch (error) {
      console.error('Error cloning field:', error)
      showNotification(
        error.response?.data?.error || 'Failed to clone field', 
        'error'
      )
    } finally {
      setLoading(false)
    }
  }

  const addFieldValue = () => {
    setFormData({
      ...formData,
      field_values: [...formData.field_values, '']
    })
  }

  const updateFieldValue = (index, value) => {
    const newValues = [...formData.field_values]
    newValues[index] = value
    setFormData({
      ...formData,
      field_values: newValues
    })
  }

  const removeFieldValue = (index) => {
    const newValues = formData.field_values.filter((_, i) => i !== index)
    setFormData({
      ...formData,
      field_values: newValues
    })
  }

  const getFieldTypeChipColor = (type) => {
    const colors = {
      condition: '#3B82F6',
      sample_preparation: '#10B981',
      treatment: '#8B5CF6',
      protocol: '#F59E0B',
      custom: '#6B7280'
    }
    return colors[type] || '#6B7280'
  }

  if (loading && !fields.length) {
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
        {/* Header Section */}
        <Paper
          elevation={1}
          sx={{
            mb: 4,
            borderRadius: 3,
            overflow: "hidden",
            border: "1px solid #E2E8F0",
          }}
        >
          <Box
            sx={{
              p: 3,
              bgcolor: getFieldColor() + "08",
              borderBottom: "1px solid #E2E8F0",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Box sx={{ display: "flex", alignItems: "center" }}>
                <IconButton
                  onClick={() => navigate(`/project/${projectId}`)}
                  sx={{ 
                    mr: 2, 
                    color: getFieldColor(),
                    '&:hover': { bgcolor: getFieldColor() + "10" }
                  }}
                >
                  <ArrowBackIcon />
                </IconButton>
                <Box>
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
                    <DataObjectIcon sx={{ mx: 1.5 }} />
                    Standardized Fields
                  </Typography>
                  {project && (
                    <Typography variant="body2" sx={{ color: "#64748B", mt: 0.5 }}>
                      {project.name} • {getFieldDisplayName()}
                    </Typography>
                  )}
                </Box>
              </Box>
              <Box sx={{ display: "flex", gap: 1 }}>
                <Chip
                  label={`${fields.length} Fields`}
                  size="small"
                  sx={{
                    bgcolor: getFieldColor() + "15",
                    color: getFieldColor(),
                    fontWeight: 500,
                  }}
                />
              </Box>
            </Box>
          </Box>
        </Paper>

        {/* Actions Section */}
        <Paper
          elevation={1}
          sx={{
            mb: 4,
            borderRadius: 3,
            border: "1px solid #E2E8F0",
            bgcolor: "#FFFFFF"
          }}
        >
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, color: "#1E293B" }}>
                Field Management
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setShowCreateForm(true)}
                sx={{
                  backgroundColor: getFieldColor(),
                  color: "white",
                  fontWeight: 500,
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
                Create New Field
              </Button>
            </Box>

            {/* Filter Section */}
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Filter by Type</InputLabel>
                  <Select
                    value={selectedFieldType}
                    onChange={(e) => setSelectedFieldType(e.target.value)}
                    label="Filter by Type"
                  >
                    <MenuItem value="all">All Types</MenuItem>
                    {fieldTypes.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        <Box sx={{ display: "flex", alignItems: "center" }}>
                          <span style={{ marginRight: 8 }}>{type.icon}</span>
                          {type.label}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: "flex", gap: 1, justifyContent: "flex-end" }}>
                  <Tooltip title="Export Fields">
                    <IconButton size="small" sx={{ color: "#64748B" }}>
                      <DownloadIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Import Fields">
                    <IconButton size="small" sx={{ color: "#64748B" }}>
                      <UploadIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Paper>

        {/* Fields List */}
        <Paper
          elevation={1}
          sx={{
            borderRadius: 3,
            border: "1px solid #E2E8F0",
            bgcolor: "#FFFFFF"
          }}
        >
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: "#1E293B", mb: 3 }}>
              Fields Library
            </Typography>

            {fields.length === 0 ? (
              <Box sx={{ textAlign: "center", py: 8 }}>
                <DataObjectIcon sx={{ fontSize: 60, color: "#94A3B8", mb: 2 }} />
                <Typography variant="h6" sx={{ color: "#64748B", mb: 1 }}>
                  No standardized fields yet
                </Typography>
                <Typography variant="body2" sx={{ color: "#94A3B8", mb: 3 }}>
                  Create your first standardized field to get started
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setShowCreateForm(true)}
                  sx={{
                    backgroundColor: getFieldColor(),
                    color: "white",
                    textTransform: "none"
                  }}
                >
                  Create Field
                </Button>
              </Box>
            ) : (
              <Grid container spacing={3}>
                {fields.map((field) => (
                  <Grid item xs={12} md={6} lg={4} key={field.progressive_id}>
                    <Card
                      sx={{
                        height: "100%",
                        borderRadius: 2,
                        border: "1px solid #E2E8F0",
                        '&:hover': {
                          borderColor: getFieldColor() + "40",
                          boxShadow: "0 4px 12px rgba(0,0,0,0.05)"
                        },
                        transition: 'all 0.3s ease'
                      }}
                    >
                      <CardContent sx={{ p: 3 }}>
                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 2 }}>
                          <Chip
                            label={fieldTypes.find(t => t.value === field.field_type)?.label || field.field_type}
                            size="small"
                            sx={{
                              backgroundColor: getFieldTypeChipColor(field.field_type) + "15",
                              color: getFieldTypeChipColor(field.field_type),
                              fontWeight: 500,
                              fontSize: "0.75rem"
                            }}
                          />
                          <Box sx={{ display: "flex", gap: 0.5 }}>
                            <Tooltip title="Edit">
                              <IconButton
                                size="small"
                                onClick={() => handleEdit(field)}
                                sx={{ color: "#64748B" }}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Clone">
                              <IconButton
                                size="small"
                                onClick={() => handleClone(field.progressive_id)}
                                sx={{ color: "#64748B" }}
                              >
                                <CloneIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton
                                size="small"
                                onClick={() => {
                                  setFieldToDelete(field)
                                  setDeleteDialogOpen(true)
                                }}
                                sx={{ color: "#EF4444" }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>

                        <Typography variant="h6" sx={{ fontWeight: 600, color: "#1E293B", mb: 1 }}>
                          {field.field_name}
                        </Typography>

                        {field.field_description && (
                          <Typography variant="body2" sx={{ color: "#64748B", mb: 2, lineHeight: 1.5 }}>
                            {field.field_description}
                          </Typography>
                        )}

                        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
                          <Chip
                            label={dataTypes.find(dt => dt.value === field.data_type)?.label || field.data_type}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: "0.7rem" }}
                          />
                          {field.is_required && (
                            <Chip
                              label="Required"
                              size="small"
                              sx={{
                                backgroundColor: "#FEF3C7",
                                color: "#D97706",
                                fontSize: "0.7rem"
                              }}
                            />
                          )}
                        </Box>

                        {field.field_values && field.field_values.length > 0 && (
                          <Box>
                            <Typography variant="caption" sx={{ color: "#94A3B8", mb: 1, display: "block" }}>
                              Values ({field.field_values.length}):
                            </Typography>
                            <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                              {field.field_values.slice(0, 3).map((value, index) => (
                                <Chip
                                  key={index}
                                  label={value}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontSize: "0.65rem", height: 20 }}
                                />
                              ))}
                              {field.field_values.length > 3 && (
                                <Chip
                                  label={`+${field.field_values.length - 3} more`}
                                  size="small"
                                  sx={{
                                    fontSize: "0.65rem",
                                    height: 20,
                                    backgroundColor: "#F1F5F9",
                                    color: "#64748B"
                                  }}
                                />
                              )}
                            </Box>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>
        </Paper>

        {/* Create/Edit Form Dialog */}
        <Dialog
          open={showCreateForm}
          onClose={resetForm}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: { borderRadius: 2 }
          }}
        >
          <DialogTitle sx={{ pb: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {editingField ? 'Edit Field' : 'Create New Field'}
            </Typography>
          </DialogTitle>
          <form onSubmit={handleSubmit}>
            <DialogContent sx={{ pt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Field Type</InputLabel>
                    <Select
                      value={formData.field_type}
                      onChange={(e) => setFormData({ ...formData, field_type: e.target.value })}
                      label="Field Type"
                    >
                      {fieldTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          <Box>
                            <Typography sx={{ fontWeight: 500 }}>
                              {type.icon} {type.label}
                            </Typography>
                            <Typography variant="caption" sx={{ color: "#64748B" }}>
                              {type.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Data Type</InputLabel>
                    <Select
                      value={formData.data_type}
                      onChange={(e) => setFormData({ ...formData, data_type: e.target.value })}
                      label="Data Type"
                    >
                      {dataTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.icon} {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Field Name"
                    value={formData.field_name}
                    onChange={(e) => setFormData({ ...formData, field_name: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Description"
                    value={formData.field_description}
                    onChange={(e) => setFormData({ ...formData, field_description: e.target.value })}
                    multiline
                    rows={3}
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.is_required}
                        onChange={(e) => setFormData({ ...formData, is_required: e.target.checked })}
                      />
                    }
                    label="Required field"
                  />
                </Grid>

                {/* Field Values Section */}
                {(formData.data_type === 'select') && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                      Field Values
                    </Typography>
                    {formData.field_values.map((value, index) => (
                      <Box key={index} sx={{ display: "flex", gap: 1, mb: 1 }}>
                        <TextField
                          fullWidth
                          size="small"
                          value={value}
                          onChange={(e) => updateFieldValue(index, e.target.value)}
                          placeholder={`Value ${index + 1}`}
                        />
                        <IconButton
                          size="small"
                          onClick={() => removeFieldValue(index)}
                          sx={{ color: "#EF4444" }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    ))}
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={addFieldValue}
                      sx={{ mt: 1 }}
                    >
                      Add Value
                    </Button>
                  </Grid>
                )}
              </Grid>
            </DialogContent>
            <DialogActions sx={{ p: 3, pt: 1 }}>
              <Button onClick={resetForm} sx={{ color: "#64748B" }}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={loading}
                sx={{
                  backgroundColor: getFieldColor(),
                  color: "white",
                  textTransform: "none",
                  '&:hover': {
                    backgroundColor: getFieldColor(),
                    filter: "brightness(0.9)"
                  }
                }}
              >
                {editingField ? 'Update Field' : 'Create Field'}
              </Button>
            </DialogActions>
          </form>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={() => setDeleteDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: "flex", alignItems: "center" }}>
              <ErrorIcon sx={{ color: "#EF4444", mr: 1 }} />
              Confirm Deletion
            </Box>
          </DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to delete the field "{fieldToDelete?.field_name}"? 
              This action cannot be undone and may affect existing data.
            </Typography>
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setDeleteDialogOpen(false)} sx={{ color: "#64748B" }}>
              Cancel
            </Button>
            <Button
              onClick={handleDelete}
              variant="contained"
              sx={{
                backgroundColor: "#EF4444",
                color: "white",
                '&:hover': { backgroundColor: "#DC2626" }
              }}
            >
              Delete Field
            </Button>
          </DialogActions>
        </Dialog>
      </Container>

      {/* Notification Snackbar */}
      <Snackbar
        open={!!notification}
        autoHideDuration={5000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        {notification && (
          <Alert
            onClose={() => setNotification(null)}
            severity={notification.type}
            sx={{ width: '100%' }}
          >
            {notification.message}
          </Alert>
        )}
      </Snackbar>
    </Box>
  )
}

export default StandardizedFieldsPage