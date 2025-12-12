// omnis_frontend/src/components/pipelines/Sidebar.js

import React from 'react';
import { Box, Typography, Button, TextField, Paper, Divider, Chip, Stack } from '@mui/material';

const NodeSidebarMetabolomics = ({
  onDragStart,
  handleRunPipeline,
  pipelineName,
  setPipelineName,
  availableNodes,
}) => {
  return (
    <Paper
      elevation={10}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        width: 280,
        px: 3,
        py: 2,
        bgcolor: 'linear-gradient(180deg, rgba(13,37,63,0.95), rgba(18,52,99,0.95))',
        color: 'common.white',
        borderRadius: 3,
        position: 'sticky',
        top: 16,
        height: 'calc(100vh - 32px)',
        overflowY: 'auto',
        boxShadow: '0 20px 60px rgba(3,10,25,0.35)',
      }}
    >
      <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold' }}>
        Pipeline Builder
      </Typography>
      <Typography variant="caption" sx={{ mb: 2, color: 'rgba(255,255,255,0.72)' }}>
        Definisci il nome e trascina i nodi per costruire il flow
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, letterSpacing: 0.5 }}>
          Nome pipeline
        </Typography>
        <TextField
          fullWidth
          size="small"
          label="Nome pipeline"
          variant="filled"
          value={pipelineName}
          onChange={(e) => setPipelineName(e.target.value)}
          InputProps={{
            sx: { bgcolor: 'rgba(255,255,255,0.12)', borderRadius: 2, color: 'common.white' },
          }}
        />
      </Box>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.2)', mb: 2 }} />

      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Libreria nodi
      </Typography>
      <Stack spacing={1} sx={{ mb: 2 }}>
        {availableNodes.map((node) => (
          <Button
            key={node.id}
            variant="outlined"
            color="inherit"
            onDragStart={(event) => onDragStart(event, node.name)}
            draggable
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderColor: 'rgba(255,255,255,0.6)',
              bgcolor: 'rgba(255,255,255,0.08)',
              color: 'primary.light',
              textTransform: 'none',
              py: 1,
              px: 2,
              borderRadius: 2,
              boxShadow: '0 6px 14px rgba(0,0,0,0.2)',
              minWidth: 'auto',
              maxWidth: '100%',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.18)' },
            }}
          >
            <Typography
              variant="body2"
              sx={{
                fontWeight: 'medium',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {node.label || node.name}
            </Typography>
            <Chip
              label={node.field}
              size="small"
              sx={{
                bgcolor: 'rgba(255,255,255,0.25)',
                color: 'common.white',
                ml: 1,
              }}
            />
          </Button>
        ))}
      </Stack>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.2)', mb: 2 }} />

      <Button
        variant="contained"
        color="secondary"
        onClick={handleRunPipeline}
        fullWidth
        sx={{ py: 1.5, fontWeight: 'bold', borderRadius: 2 }}
      >
        Run Pipeline
      </Button>
      <Typography variant="caption" sx={{ mt: 1, color: 'rgba(255,255,255,0.7)' }}>
        Verrà eseguito solo il flusso collegato dal nodo iniziale e nell’ordine di connessione.
      </Typography>
    </Paper>
  );
};

export default NodeSidebarMetabolomics;