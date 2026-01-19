"use client"

import api from "../../utils/ApiFlowCytometry"
import { useEffect, useState, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  CircularProgress,
  TextField,
  Tooltip,
  Alert,
  Fade,
  InputAdornment,
  Card,
  CardHeader,
  CardContent,
  Checkbox,
  Select,
  MenuItem,
} from "@mui/material"
import DeleteIcon from "@mui/icons-material/Delete"
import SearchIcon from "@mui/icons-material/Search"
import ScienceIcon from "@mui/icons-material/Science"
import WarningIcon from "@mui/icons-material/Warning"
import VisibilityIcon from "@mui/icons-material/Visibility"


const CytometryTable = ({ projectId, projectName }) => {
  const [experiments, setExperiments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState("")
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteAllDialogOpen, setDeleteAllDialogOpen] = useState(false)
  const [selectedExperiments, setSelectedExperiments] = useState([])
  const [confirmationText, setConfirmationText] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [savingControl, setSavingControl] = useState({})

  const navigate = useNavigate()

  // Wrap fetchExperiments in useCallback
  const fetchExperiments = useCallback(async () => {
    try {
      console.log("Making request to:", api.defaults.baseURL + "/api/v1/project/1/flow_cytometry");
      const response = await api.get(`/api/v1/project/${projectId}/flow_cytometry`)
      if (response.data.message) {
        setMessage(response.data.message)
      }
      setExperiments(response.data.data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchExperiments()
  }, [fetchExperiments])

  const handleDeleteSelected = async () => {
    try {
      await api.delete(`/api/v1/project/${projectId}/flow_cytometry/batch_delete`, {
        data: { fcs_ids: selectedExperiments },
      })
      setMessage("Selected experiments deleted successfully")
      fetchExperiments()
      setSelectedExperiments([])
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDeleteAll = async () => {
    if (confirmationText.trim().toLowerCase() !== projectName.trim().toLowerCase()) {
      setError("Project name does not match. Please type the project name correctly.")
      return
    }
    try {
      const allIds = experiments.map((exp) => exp.progressive_id)
      await api.delete(`/api/v1/project/${projectId}/flow_cytometry/batch_delete`, {
        data: { fcs_ids: allIds },
      })
      setMessage("All experiments deleted successfully")
      fetchExperiments()
      setDeleteAllDialogOpen(false)
      setConfirmationText("")
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSelectExperiment = (id) => {
    setSelectedExperiments((prev) =>
      prev.includes(id) ? prev.filter((expId) => expId !== id) : [...prev, id],
    )
  }

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedExperiments(experiments.map((exp) => exp.progressive_id))
    } else {
      setSelectedExperiments([])
    }
  }

  const handleOpenDeleteDialog = (id) => {
    setSelectedExperiments([id]) // Set the selected experiment for deletion
    setDeleteDialogOpen(true)   // Open the delete dialog
  }

  const handleSetControl = async (experimentId, controlId) => {
    setSavingControl((prev) => ({ ...prev, [experimentId]: true }))
    try {
      await api.put(
        `/api/v1/project/${projectId}/flow_cytometry/${experimentId}/control`,
        { control_id: controlId }
      )
      setMessage("Control sample updated successfully")
      fetchExperiments()
    } catch (err) {
      let errorMsg = "Unknown error";
      if (err.response && err.response.data && err.response.data.error) {
        errorMsg = err.response.data.error;
      } else if (err.response && err.response.status) {
        errorMsg = `API error: ${err.response.status}`;
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg)
    } finally {
      setSavingControl((prev) => ({ ...prev, [experimentId]: false }))
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: 300 }}>
        <CircularProgress size={40} />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" icon={<WarningIcon fontSize="inherit" />} sx={{ mb: 2, borderRadius: 2 }}>
        {error}
      </Alert>
    )
  }

  return (
    <Card elevation={2} sx={{ borderRadius: 2, overflow: "hidden" }}>
      <CardHeader
        title={
          <Typography variant="h6" sx={{ fontWeight: "bold", display: "flex", alignItems: "center" }}>
            <ScienceIcon sx={{ mr: 1 }} /> Flow Cytometry Experiments
          </Typography>
        }
        sx={{
          bgcolor: "primary.main",
          color: "primary.contrastText",
          py: 1.5,
        }}
      />

      <CardContent sx={{ p: 0 }}>
        {message && (
          <Fade in={Boolean(message)}>
            <Alert severity="success" sx={{ mx: 2, mt: 2, borderRadius: 1 }} onClose={() => setMessage("")}>
              {message}
            </Alert>
          </Fade>
        )}

        <Box sx={{ p: 2 }}>
          <TextField
            label="Search by Filename"
            variant="outlined"
            fullWidth
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="action" />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />

          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
            <Button
              variant="contained"
              color="error"
              onClick={() => setDeleteAllDialogOpen(true)}
              disabled={experiments.length === 0}
            >
              Delete All
            </Button>
            <Button
              variant="contained"
              color="error"
              onClick={handleDeleteSelected}
              disabled={selectedExperiments.length === 0}
            >
              Delete Selected
            </Button>
          </Box>

          <TableContainer
            component={Paper}
            sx={{ maxHeight: 400, borderRadius: 1, boxShadow: "none", border: "1px solid", borderColor: "divider" }}
          >
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      indeterminate={
                        selectedExperiments.length > 0 && selectedExperiments.length < experiments.length
                      }
                      checked={selectedExperiments.length === experiments.length}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                  </TableCell>
                  <TableCell sx={{ bgcolor: "background.default", fontWeight: "bold" }}>ID</TableCell>
                  <TableCell sx={{ bgcolor: "background.default", fontWeight: "bold" }}>Name</TableCell>
                  <TableCell sx={{ bgcolor: "background.default", fontWeight: "bold" }}>Control Sample</TableCell>
                  <TableCell sx={{ bgcolor: "background.default", fontWeight: "bold", width: 150 }}>
                    Actions
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {experiments.map((experiment) => (
                  <TableRow key={experiment.progressive_id}>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedExperiments.includes(experiment.progressive_id)}
                        onChange={() => handleSelectExperiment(experiment.progressive_id)}
                      />
                    </TableCell>
                    <TableCell>{experiment.progressive_id}</TableCell>
                    <TableCell>{experiment.filename}</TableCell>
                    {/* Control Sample Select */}
                    <TableCell>
                      <Select
                        value={experiment.control_id ?? ""}
                        onChange={(e) => handleSetControl(experiment.progressive_id, e.target.value)}
                        size="small"
                        disabled={Boolean(savingControl[experiment.progressive_id])}
                        displayEmpty
                        fullWidth
                      >
                        <MenuItem value="">None</MenuItem>
                        {experiments
                          .filter((ex) => ex.progressive_id !== experiment.progressive_id)
                          .map((ex) => (
                            <MenuItem key={ex.progressive_id} value={ex.progressive_id}>
                              {ex.filename}
                            </MenuItem>
                          ))}
                      </Select>
                    </TableCell>
                    <TableCell>
                      {/* Gating strategies action */}
                      <Tooltip title="View Gating Strategies">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() =>
                            navigate(`/project/${projectId}/fcs_object/${experiment.progressive_id}/gatingStrategies`)
                          }
                        >
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {/* Delete action */}
                      <Tooltip title="Delete Experiment">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleOpenDeleteDialog(experiment.progressive_id)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </CardContent>

      <Dialog
        open={deleteAllDialogOpen}
        onClose={() => setDeleteAllDialogOpen(false)}
        PaperProps={{
          sx: { borderRadius: 2 },
        }}
      >
        <DialogTitle>Delete All Experiments</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete all experiments? This action cannot be undone.
          </Typography>
          <Typography sx={{ mt: 1, fontWeight: "bold", color: "error.main" }}>
            To confirm, type the project name: <strong>{projectName}</strong>
          </Typography>
          <TextField
            fullWidth
            label="Type the project name to confirm"
            value={confirmationText}
            onChange={(e) => setConfirmationText(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAllDialogOpen(false)} variant="outlined">
            Cancel
          </Button>
          <Button
            onClick={handleDeleteAll}
            variant="contained"
            color="error"
            disabled={confirmationText.trim().toLowerCase() !== projectName.trim().toLowerCase()} // Case-insensitive comparison
          >
            Delete All
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  )
}

export default CytometryTable

