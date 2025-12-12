import { useState } from "react"
import flowCytometryApi from '../../utils/ApiFlowCytometry';
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

const BatchFlowCytometryUpload = () => {
  const { progressive_id } = useParams()
  const theme = useTheme()
  const defaultTheme = createTheme()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [fcsFiles, setFcsFiles] = useState([]);
  const [wspFiles, setWspFiles] = useState([]);
  const [metadataFile, setMetadataFile] = useState(null);
  const [message, setMessage] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [duplicateFiles, setDuplicateFiles] = useState([]);
  const [validationError, setValidationError] = useState('');

  const handleFcsFileChange = (e) => {
    setFcsFiles(Array.from(e.target.files));
    if (e.target.files.length > 0) {
      setValidationError('');
    }
  };

  const handleWspFileChange = (e) => {
    setWspFiles(Array.from(e.target.files));
  };

  const handleMetadataChange = (e) => {
    setMetadataFile(e.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const fcs = files.filter((file) => file.name.endsWith('.fcs'));
    const wsp = files.filter((file) => file.name.endsWith('.wsp'));
    if (fcs.length > 0) {
      setFcsFiles((prev) => [...prev, ...fcs]);
      setValidationError('');
    }
    if (wsp.length > 0) {
      setWspFiles((prev) => [...prev, ...wsp]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation: Ensure at least one FCS file is uploaded
    if (fcsFiles.length === 0) {
      setValidationError('Please upload at least one FCS file.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);
    setDuplicateFiles([]);
    setMessage('');

    const formData = new FormData();
    formData.append('project_id', progressive_id);

    fcsFiles.forEach((file) => {
      formData.append('cytofluorimetry_files', file);
    });

    if (wspFiles.length > 0) {
      wspFiles.forEach((file) => {
        formData.append('wsp_files', file);
      });
    }

    if (metadataFile) {
      formData.append('metadata_file', metadataFile);
    }

    try {
      const response = await flowCytometryApi.post(
        `/api/v1/project/${progressive_id}/flow_cytometry/batch`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setResults(response.data.results);
      setMessage(response.data.message);
      setSuccess(true);
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Error uploading files';
      setMessage(errorMessage);
      setResults([]);
      setError(errorMessage);

      if (error.response?.data?.duplicates) {
        setDuplicateFiles(error.response.data.duplicates);
      }

      console.error('Error uploading files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadExcel = () => {
    const data = fcsFiles.map((file, index) => ({
      Nome: file.name,
      Workspace: wspFiles[index] ? wspFiles[index].name : '', // Placeholder for user to fill in the metadata
    }));

    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Metadata');

    XLSX.writeFile(workbook, 'metadata_schema.xlsx');
  };

  // Determine current step
  const getCurrentStep = () => {
    if (success) return 2
    if (fcsFiles.length > 0) return 1
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
              <ScienceIcon fontSize="large" /> Flow Cytometry Data Upload
            </Typography>
            <Typography variant="subtitle1" sx={{ mt: 1, opacity: 0.9 }}>
              Upload your FCS files and workspace files for analysis
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
                    FCS Files
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
                      Drag and drop FCS files here
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      or
                    </Typography>
                    <input
                      type="file"
                      multiple
                      onChange={handleFcsFileChange}
                      accept=".fcs"
                      style={{ display: "none" }}
                      id="fcs-files-input"
                    />
                    <label htmlFor="fcs-files-input">
                      <Button variant="contained" component="span" startIcon={<FileUploadIcon />} sx={{ mt: 1 }}>
                        Select FCS Files
                      </Button>
                    </label>
                  </DropZone>

                  {/* WSP Files Section */}
                  <Typography variant="h6" fontWeight="600" gutterBottom>
                    WSP Files (Optional)
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
                      Drag and drop WSP files here
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      or
                    </Typography>
                    <input
                      type="file"
                      multiple
                      onChange={handleWspFileChange}
                      accept=".wsp"
                      style={{ display: "none" }}
                      id="wsp-files-input"
                    />
                    <label htmlFor="wsp-files-input">
                      <Button variant="contained" component="span" startIcon={<FileUploadIcon />} sx={{ mt: 1 }}>
                        Select WSP Files
                      </Button>
                    </label>
                  </DropZone>

                  {/* Selected Files Display */}
                  {fcsFiles.length > 0 && (
                    <Card variant="outlined" sx={{ mb: 3, borderRadius: "8px" }}>
                      <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                          <Typography variant="subtitle1" fontWeight="600">
                            Selected FCS Files ({fcsFiles.length})
                          </Typography>
                          <Chip
                            label={`${fcsFiles.length} file${fcsFiles.length !== 1 ? "s" : ""}`}
                            color="primary"
                            size="small"
                          />
                        </Box>
                        <List sx={{ maxHeight: "200px", overflow: "auto" }}>
                          {fcsFiles.map((file, index) => (
                            <FileItem key={index}>
                              <DescriptionIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
                              <ListItemText
                                primary={file.name}
                                secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                              />
                              <IconButton
                                edge="end"
                                onClick={() => {
                                  setFcsFiles(fcsFiles.filter((_, i) => i !== index))
                                }}
                                size="small"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </FileItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  )}

                  {/* WSP Files Display */}
                  {wspFiles.length > 0 && (
                    <Card variant="outlined" sx={{ mb: 3, borderRadius: "8px" }}>
                      <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                          <Typography variant="subtitle1" fontWeight="600">
                            Selected WSP Files ({wspFiles.length})
                          </Typography>
                          <Chip
                            label={`${wspFiles.length} file${wspFiles.length !== 1 ? "s" : ""}`}
                            color="primary"
                            size="small"
                          />
                        </Box>
                        <List sx={{ maxHeight: "200px", overflow: "auto" }}>
                          {wspFiles.map((file, index) => (
                            <FileItem key={index}>
                              <DescriptionIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
                              <ListItemText
                                primary={file.name}
                                secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                              />
                              <IconButton
                                edge="end"
                                onClick={() => {
                                  setWspFiles(wspFiles.filter((_, i) => i !== index))
                                }}
                                size="small"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </FileItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  )}
                </Grid>

                {/* Right Column - Metadata and Upload */}
                <Grid item xs={12} md={5}>
                  {/* Metadata File Upload */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body1">Upload Metadata File (optional)</Typography>
                    <input
                      type="file"
                      onChange={handleMetadataChange}
                      accept=".csv, .xls, .xlsx"
                      style={{ display: 'none' }}
                      id="metadata-file-input"
                    />
                    <label htmlFor="metadata-file-input">
                      <Button variant="contained" component="span" sx={{ mt: 1 }}>
                        Upload Metadata
                      </Button>
                    </label>
                  </Box>

                  {/* Download Metadata Schema */}
                  <Button
                    variant="contained"
                    onClick={handleDownloadExcel}
                    sx={{ mt: 2, mr: 2 }}
                  >
                    Download Metadata Schema
                  </Button>

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={loading}
                    sx={{ mt: 2 }}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Upload'}
                  </Button>

                  {/* Display Message */}
                  {message && (
                    <Typography
                      color={success ? 'success.main' : 'error.main'}
                      sx={{ mt: 2 }}
                    >
                      {message}
                    </Typography>
                  )}

                  {/* Display Duplicate Files */}
                  {duplicateFiles.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="h6" color="error">
                        Duplicate Files:
                      </Typography>
                      <List>
                        {duplicateFiles.map((file, index) => (
                          <ListItem key={index}>
                            <ListItemText primary={file} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}

                  {/* Display Upload Results */}
                  {results.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="h6">Upload Results:</Typography>
                      <ul>
                        {results.map((result, index) => (
                          <li key={index}>
                            {result.filename}: {result.status}
                          </li>
                        ))}
                      </ul>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </ThemeProvider>
  )
}

export default BatchFlowCytometryUpload