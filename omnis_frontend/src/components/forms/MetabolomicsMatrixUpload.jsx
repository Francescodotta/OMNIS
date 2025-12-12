import { useState } from "react"
import metabolomicsApi from '../../utils/ApiMetabolomics'
import {
  Button,
  Box,
  Typography,
  CircularProgress,
  Paper,
  Alert,
  Container,
  Grid,
  Card,
  CardContent,
  IconButton,
  LinearProgress,
  useTheme,
  alpha,
} from "@mui/material"
import { styled } from "@mui/system"
import { useParams } from "react-router-dom"
import Navbar from "../Navbar"
import CloudUploadIcon from "@mui/icons-material/CloudUpload"
import FileUploadIcon from "@mui/icons-material/FileUpload"
import DescriptionIcon from "@mui/icons-material/Description"
import DeleteIcon from "@mui/icons-material/Delete"
import CheckCircleIcon from "@mui/icons-material/CheckCircle"
import ErrorIcon from "@mui/icons-material/Error"
import { ThemeProvider, createTheme } from "@mui/material/styles"

const DropZone = styled(Paper)(({ theme }) => {
  const primary = theme?.palette?.primary?.main || "#1976d2"
  const hoverBg = theme?.palette?.action?.hover || "#f5f5f5"
  return ({
    padding: "24px",
    textAlign: "center",
    border: `2px dashed ${primary}`,
    backgroundColor: alpha(primary, 0.04),
    cursor: "pointer",
    borderRadius: "8px",
    transition: "all 0.2s ease",
    "&:hover": {
      backgroundColor: alpha(primary, 0.08),
      transform: "translateY(-2px)",
      boxShadow: theme?.shadows?.[2] || "0px 4px 8px rgba(0,0,0,0.08)",
    },
  })
})

const MetabolomicsMatrixUpload = () => {
  const { progressive_id } = useParams()
  const [matrixFile, setMatrixFile] = useState(null)
  const [experimentName, setExperimentName] = useState("")
  const [loading, setLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [message, setMessage] = useState("")
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  const theme = useTheme()

  const handleMatrixFileChange = (e) => {
    setMatrixFile(e.target.files[0])
  }

  const handleRemoveMatrixFile = () => {
    setMatrixFile(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!matrixFile || !experimentName) {
      setError("Please provide both the experiment name and a matrix file.")
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(false)
    setMessage("")
    setUploadProgress(0)

    const formData = new FormData()
    formData.append("matrix_file", matrixFile)
    formData.append("experiment_name", experimentName)

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          const newProgress = prev + 5
          return newProgress >= 90 ? 90 : newProgress
        })
      }, 300)

      const response = await metabolomicsApi.post(
        `/api/v1/project/${progressive_id}/matrix`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      )

      clearInterval(progressInterval)
      setUploadProgress(100)

      setMessage(response.data?.message || "Upload completed")
      setSuccess(true)
    } catch (err) {
      const errorMessage = err.response?.data?.error || "Error uploading matrix file"
      setMessage(errorMessage)
      setError(errorMessage)
      console.error("Error uploading matrix file:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />
      <Container maxWidth="md" sx={{ mt: 4, mb: 8 }}>
        <Card elevation={1} sx={{ borderRadius: 2 }}>
          <Box
            sx={{
              p: 2.5,
              backgroundColor: (t) => t?.palette?.primary?.main || "#1976d2",
              color: "white",
              borderTopLeftRadius: 8,
              borderTopRightRadius: 8,
            }}
          >
            <Typography variant="h5" fontWeight={600}>
              Upload Metabolomics Matrix
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.9 }}>
              Upload your matrix file (Excel, CSV, TSV)
            </Typography>
          </Box>

          <CardContent sx={{ p: 3 }}>
            <Box component="form" onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Experiment Name
                  </Typography>
                  <input
                    type="text"
                    value={experimentName}
                    onChange={(e) => setExperimentName(e.target.value)}
                    placeholder="Enter experiment name"
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: 6,
                      border: "1px solid #ddd",
                      marginBottom: 12,
                    }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Matrix File
                  </Typography>
                  <DropZone>
                    <input
                      type="file"
                      onChange={handleMatrixFileChange}
                      accept=".csv, .tsv, .xls, .xlsx"
                      style={{ display: "none" }}
                      id="matrix-file-input"
                    />
                    <label htmlFor="matrix-file-input">
                      <Button variant="contained" component="span" startIcon={<FileUploadIcon />}>
                        Select Matrix File
                      </Button>
                    </label>
                  </DropZone>

                  {matrixFile && (
                    <Box
                      sx={{
                        mt: 2,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        p: 2,
                        bgcolor: "background.paper",
                        borderRadius: 1,
                        boxShadow: 1,
                      }}
                    >
                      <Box sx={{ display: "flex", alignItems: "center" }}>
                        <DescriptionIcon sx={{ mr: 1, color: "text.secondary" }} />
                        <Typography variant="body2">{matrixFile.name}</Typography>
                      </Box>
                      <IconButton onClick={handleRemoveMatrixFile} sx={{ color: "error.main" }}>
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  )}
                </Grid>
              </Grid>

              <Box sx={{ mt: 3 }}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                  fullWidth
                  size="large"
                  startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <CloudUploadIcon />}
                >
                  {loading ? "Uploading..." : "Upload Matrix"}
                </Button>

                {loading && (
                  <Box sx={{ mt: 2 }}>
                    <LinearProgress variant="determinate" value={uploadProgress} />
                    <Typography variant="caption" align="center" display="block" sx={{ mt: 1 }}>
                      Uploading... {uploadProgress}%
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>

            {message && (
              <Alert
                severity={success ? "success" : "error"}
                icon={success ? <CheckCircleIcon /> : <ErrorIcon />}
                sx={{ mt: 3 }}
              >
                {message}
              </Alert>
            )}
          </CardContent>
        </Card>
      </Container>
    </>
  )
}

export default MetabolomicsMatrixUpload