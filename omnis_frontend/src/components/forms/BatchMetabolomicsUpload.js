"use client"

import { useState } from "react"
import metabolomicsApi from "../../utils/ApiMetabolomics"
import {
  Button,
  Box,
  Typography,
  CircularProgress,
  Paper,
  List,
  ListItem,
  ListItemText,
  Alert,
  Container,
  Grid,
  Card,
  CardContent,
  Divider,
  Chip,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  Tooltip,
  LinearProgress,
  useTheme,
  alpha,
} from "@mui/material"
import { styled } from "@mui/system"
import * as XLSX from "xlsx"
import { useParams } from "react-router-dom"
import Navbar from "../Navbar"
import CloudUploadIcon from "@mui/icons-material/CloudUpload"
import FileUploadIcon from "@mui/icons-material/FileUpload"
import DescriptionIcon from "@mui/icons-material/Description"
import DeleteIcon from "@mui/icons-material/Delete"
import CheckCircleIcon from "@mui/icons-material/CheckCircle"
import ErrorIcon from "@mui/icons-material/Error"
import DownloadIcon from "@mui/icons-material/Download"
import ScienceIcon from "@mui/icons-material/Science"
import { ThemeProvider, createTheme } from "@mui/material/styles"

const DropZone = styled(Paper)(({ theme }) => ({
  padding: "32px",
  textAlign: "center",
  border: `2px dashed ${theme.palette.primary.main}`,
  backgroundColor: alpha(theme.palette.primary.main, 0.05),
  cursor: "pointer",
  borderRadius: "12px",
  transition: "all 0.3s ease",
  "&:hover": {
    backgroundColor: alpha(theme.palette.primary.main, 0.1),
    transform: "translateY(-2px)",
    boxShadow: theme.shadows[4],
  },
}))

const FileItem = styled(ListItem)(({ theme }) => ({
  backgroundColor: alpha(theme.palette.background.paper, 0.7),
  borderRadius: "8px",
  marginBottom: "8px",
  boxShadow: theme.shadows[1],
  transition: "all 0.2s ease",
  "&:hover": {
    backgroundColor: theme.palette.background.paper,
    boxShadow: theme.shadows[2],
  },
}))

const UploadButton = styled(Button)(({ theme }) => ({
  padding: "10px 24px",
  borderRadius: "8px",
  fontWeight: 600,
  boxShadow: theme.shadows[2],
  transition: "all 0.3s ease",
  "&:hover": {
    transform: "translateY(-2px)",
    boxShadow: theme.shadows[4],
  },
}))

const BatchMetabolomicsUpload = () => {
  const { progressive_id } = useParams()
  const [rawFiles, setRawFiles] = useState([])
  const [metadataFile, setMetadataFile] = useState(null)
  const [message, setMessage] = useState("")
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [duplicateFiles, setDuplicateFiles] = useState([])
  const [validationError, setValidationError] = useState("")
  const [uploadProgress, setUploadProgress] = useState(0)
  const theme = useTheme()

  const defaultTheme = createTheme()

  console.log(progressive_id)

  const handleRawFileChange = (e) => {
    setRawFiles(Array.from(e.target.files))
    if (e.target.files.length > 0) {
      setValidationError("")
    }
  }

  const handleMetadataChange = (e) => {
    setMetadataFile(e.target.files[0])
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    const raw = files.filter((file) => file.name.endsWith(".raw"))
    if (raw.length > 0) {
      setRawFiles((prev) => [...prev, ...raw])
      setValidationError("")
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleRemoveFile = (index) => {
    setRawFiles((prevFiles) => prevFiles.filter((_, i) => i !== index))
  }

  const handleRemoveMetadata = () => {
    setMetadataFile(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Validation: Ensure at least one RAW file is uploaded
    if (rawFiles.length === 0) {
      setValidationError("Please upload at least one RAW file.")
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(false)
    setDuplicateFiles([])
    setMessage("")
    setUploadProgress(0)

    const formData = new FormData()
    formData.append("project_id", progressive_id)

    rawFiles.forEach((file) => {
      formData.append("metabolomics_files", file)
    })

    if (metadataFile) {
      formData.append("metadata_file", metadataFile)
    }

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          const newProgress = prev + 5
          return newProgress >= 90 ? 90 : newProgress
        })
      }, 300)

      const response = await metabolomicsApi.post(
        `/api/v1/project/${progressive_id}/metabolomics_experiments`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      )

      clearInterval(progressInterval)
      setUploadProgress(100)

      setResults(response.data.results)
      setMessage(response.data.message)
      setSuccess(true)
    } catch (error) {
      const errorMessage = error.response?.data?.error || "Error uploading files"
      setMessage(errorMessage)
      setResults([])
      setError(errorMessage)

      if (error.response?.data?.duplicates) {
        setDuplicateFiles(error.response.data.duplicates)
      }

      console.error("Error uploading files:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadExcel = () => {
    const data = rawFiles.map((file) => ({
      "File Name": file.name,
      Conditions: "", // Empty column for user to fill
      "Sample Type": "", // Empty column for user to fill
    }))

    const worksheet = XLSX.utils.json_to_sheet(data)
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, "Metadata")

    XLSX.writeFile(workbook, "metabolomics_metadata_schema.xlsx")
  }

  // Determine current step
  const getCurrentStep = () => {
    if (success) return 2
    if (rawFiles.length > 0) return 1
    return 0
  }

  return (
    <ThemeProvider theme={defaultTheme}>
      <Navbar />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
        <Card elevation={3} sx={{ borderRadius: "12px", overflow: "visible" }}>
          <Box
            sx={{
              p: 3,
              background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
              borderTopLeftRadius: "12px",
              borderTopRightRadius: "12px",
              color: "white",
            }}
          >
            <Typography variant="h4" fontWeight="bold" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <ScienceIcon fontSize="large" /> Metabolomics Data Upload
            </Typography>
            <Typography variant="subtitle1" sx={{ mt: 1, opacity: 0.9 }}>
              Upload your metabolomics RAW files and metadata for analysis
            </Typography>
          </Box>

          <CardContent sx={{ p: 4 }}>
            <Stepper activeStep={getCurrentStep()} sx={{ mb: 4 }}>
              <Step>
                <StepLabel>Select Files</StepLabel>
              </Step>
              <Step>
                <StepLabel>Configure Metadata</StepLabel>
              </Step>
              <Step>
                <StepLabel>Upload Complete</StepLabel>
              </Step>
            </Stepper>

            <Box component="form" onSubmit={handleSubmit}>
              <Grid container spacing={4}>
                <Grid item xs={12} md={7}>
                  <Typography variant="h6" fontWeight="600" gutterBottom>
                    RAW Files
                  </Typography>

                  <DropZone
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    sx={{
                      mb: 3,
                      height: "200px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                    }}
                  >
                    <CloudUploadIcon sx={{ fontSize: 48, color: theme.palette.primary.main, mb: 2 }} />
                    <Typography variant="body1" gutterBottom>
                      Drag and drop RAW files here
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      or
                    </Typography>
                    <input
                      type="file"
                      multiple
                      onChange={handleRawFileChange}
                      accept=".raw"
                      style={{ display: "none" }}
                      id="raw-files-input"
                    />
                    <label htmlFor="raw-files-input">
                      <Button variant="contained" component="span" startIcon={<FileUploadIcon />} sx={{ mt: 1 }}>
                        Select RAW Files
                      </Button>
                    </label>
                  </DropZone>

                  {validationError && (
                    <Alert
                      severity="error"
                      sx={{
                        mb: 3,
                        borderRadius: "8px",
                        boxShadow: theme.shadows[2],
                      }}
                    >
                      {validationError}
                    </Alert>
                  )}

                  {rawFiles.length > 0 && (
                    <Card variant="outlined" sx={{ mb: 3, borderRadius: "8px" }}>
                      <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                          <Typography variant="subtitle1" fontWeight="600">
                            Selected RAW Files ({rawFiles.length})
                          </Typography>
                          <Chip
                            label={`${rawFiles.length} file${rawFiles.length !== 1 ? "s" : ""}`}
                            color="primary"
                            size="small"
                          />
                        </Box>
                        <Divider sx={{ mb: 2 }} />
                        <List sx={{ maxHeight: "200px", overflow: "auto", pr: 1 }}>
                          {rawFiles.map((file, index) => (
                            <FileItem key={index}>
                              <DescriptionIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
                              <ListItemText
                                primary={file.name}
                                secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                              />
                              <Tooltip title="Remove file">
                                <IconButton
                                  edge="end"
                                  aria-label="delete"
                                  onClick={() => handleRemoveFile(index)}
                                  size="small"
                                  sx={{ color: theme.palette.error.main }}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Tooltip>
                            </FileItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  )}
                </Grid>

                <Grid item xs={12} md={5}>
                  <Typography variant="h6" fontWeight="600" gutterBottom>
                    Metadata
                  </Typography>

                  <Card variant="outlined" sx={{ mb: 3, borderRadius: "8px" }}>
                    <CardContent>
                      <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                        Upload Metadata File (optional)
                      </Typography>

                      {metadataFile ? (
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            p: 2,
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            borderRadius: "8px",
                          }}
                        >
                          <Box sx={{ display: "flex", alignItems: "center" }}>
                            <DescriptionIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
                            <Box>
                              <Typography variant="body2" fontWeight="500">
                                {metadataFile.name}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {(metadataFile.size / 1024).toFixed(2)} KB
                              </Typography>
                            </Box>
                          </Box>
                          <IconButton
                            size="small"
                            onClick={handleRemoveMetadata}
                            sx={{ color: theme.palette.error.main }}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      ) : (
                        <Box sx={{ textAlign: "center", py: 2 }}>
                          <input
                            type="file"
                            onChange={handleMetadataChange}
                            accept=".csv, .xls, .xlsx"
                            style={{ display: "none" }}
                            id="metadata-file-input"
                          />
                          <label htmlFor="metadata-file-input">
                            <Button variant="outlined" component="span" startIcon={<FileUploadIcon />} fullWidth>
                              Select Metadata File
                            </Button>
                          </label>
                        </Box>
                      )}

                      <Divider sx={{ my: 3 }} />

                      <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                        Need a template?
                      </Typography>
                      <Button
                        variant="outlined"
                        onClick={handleDownloadExcel}
                        startIcon={<DownloadIcon />}
                        fullWidth
                        sx={{ mt: 1 }}
                      >
                        Download Metadata Template
                      </Button>
                    </CardContent>
                  </Card>

                  <Box sx={{ mt: 4 }}>
                    <UploadButton
                      type="submit"
                      variant="contained"
                      disabled={loading}
                      fullWidth
                      size="large"
                      startIcon={loading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
                    >
                      {loading ? "Uploading..." : "Upload Files"}
                    </UploadButton>

                    {loading && (
                      <Box sx={{ mt: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={uploadProgress}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="caption" align="center" display="block" sx={{ mt: 1 }}>
                          Uploading... {uploadProgress}%
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </Grid>
              </Grid>
            </Box>

            {/* Results Section */}
            {(message || results.length > 0 || duplicateFiles.length > 0) && (
              <Box sx={{ mt: 4 }}>
                <Divider sx={{ mb: 4 }} />
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  Upload Results
                </Typography>

                {message && (
                  <Alert
                    severity={success ? "success" : "error"}
                    icon={success ? <CheckCircleIcon /> : <ErrorIcon />}
                    sx={{
                      mb: 3,
                      borderRadius: "8px",
                      boxShadow: theme.shadows[2],
                    }}
                  >
                    <Typography variant="subtitle2">{message}</Typography>
                  </Alert>
                )}

                {duplicateFiles.length > 0 && (
                  <Card variant="outlined" sx={{ mb: 3, borderRadius: "8px", borderColor: theme.palette.error.main }}>
                    <CardContent>
                      <Typography variant="subtitle1" color="error" fontWeight="600">
                        Duplicate Files Detected
                      </Typography>
                      <Divider sx={{ my: 1 }} />
                      <List dense>
                        {duplicateFiles.map((file, index) => (
                          <ListItem key={index}>
                            <ErrorIcon sx={{ mr: 1, color: theme.palette.error.main, fontSize: 20 }} />
                            <ListItemText primary={file} />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                )}

                {results.length > 0 && (
                  <Card variant="outlined" sx={{ borderRadius: "8px" }}>
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="600" gutterBottom>
                        Processed Files
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      <List>
                        {results.map((result, index) => (
                          <FileItem key={index}>
                            {result.status === "success" ? (
                              <CheckCircleIcon sx={{ mr: 1, color: theme.palette.success.main }} />
                            ) : (
                              <ErrorIcon sx={{ mr: 1, color: theme.palette.error.main }} />
                            )}
                            <ListItemText primary={result.filename} secondary={result.status} />
                          </FileItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      </Container>
    </ThemeProvider>
  )
}

export default BatchMetabolomicsUpload
