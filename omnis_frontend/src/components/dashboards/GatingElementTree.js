import React, { useEffect, useState } from 'react';
import { 
  CircularProgress, 
  Typography, 
  List, 
  ListItem, 
  ListItemText, 
  Collapse, 
  Box 
} from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../utils/ApiFlowCytometry';



const GatingElementTree = ({ onGateSelect }) => {
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { projectId, progressiveId, gatingStrategyId } = useParams();


  useEffect(() => {
    const fetchTreeData = async () => {
      try {
        const response = await api.get(`/flow_cytometry/api/v1/project/${projectId}/flow_cytometry/${progressiveId}/gating_strategies/${gatingStrategyId}/gating_elements`);
        console.log(response.data.data);
        setTreeData(response.data.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTreeData();
  }, [gatingStrategyId]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" p={2}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={2}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  // Ensure we have a valid root node to render
  const rootNode = treeData && treeData.length > 0 ? treeData[0] : {
    name: 'No Gating Elements',
    progressive_id: null,
    children: []
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Gating Element Tree
      </Typography>
      <GatingElementTreeNode 
        node={rootNode} 
        onGateSelect={onGateSelect}
      />
    </Box>
  );
};

const GatingElementTreeNode = ({ node, onGateSelect }) => {
  const [open, setOpen] = React.useState(true);
  const navigate = useNavigate();
  const { projectId, progressiveId, gatingStrategyId } = useParams();

  const handleClick = (e) => {
    e.stopPropagation();
    console.log("Node clicked:", node); // Debug log
    
    // If node has children, toggle expansion
    if (node.children && node.children.length > 0) {
      setOpen(!open);
    }
    
    // Check if the clicked node is the root node
    if (node.progressive_id === null) {
      // Navigate without query parameters for the root node
      const newUrl = `/project/${projectId}/fcs_object/${progressiveId}/gating_strategies/${gatingStrategyId}/gating_elements`;
      console.log("Navigating to root:", newUrl);
      navigate(newUrl, { replace: true });
    } else {
      // Navigate with the parentId query parameter for other nodes
      const newUrl = `/project/${projectId}/fcs_object/${progressiveId}/gating_strategies/${gatingStrategyId}/gating_elements?parentId=${node.progressive_id}`;
      console.log("Navigating to:", newUrl);
      navigate(newUrl, { replace: true });
    }
  };

  // Render nothing if node is undefined
  if (!node) return null;

  return (
    <List component="div" disablePadding>
      <ListItem 
        button 
        onClick={handleClick}
        sx={{ 
          backgroundColor: node.progressive_id === null ? 'rgba(0,0,0,0.05)' : 'transparent',
          '&:hover': { backgroundColor: 'rgba(0,0,0,0.1)' }
        }}
      >
        <ListItemText 
          primary={node.name || 'Unnamed Element'} 
          secondary={node.children ? `${node.children.length} child elements` : ''}
        />
        {node.children && node.children.length > 0 ? (
          open ? <ExpandLess /> : <ExpandMore />
        ) : null}
      </ListItem>
      
      {node.children && node.children.length > 0 && (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List component="div" disablePadding sx={{ pl: 2 }}>
            {node.children.map((child) => (
              <GatingElementTreeNode 
                key={child.progressive_id || Math.random()} 
                node={child}
                onGateSelect={onGateSelect}
              />
            ))}
          </List>
        </Collapse>
      )}
    </List>
  );
};

export default GatingElementTree;