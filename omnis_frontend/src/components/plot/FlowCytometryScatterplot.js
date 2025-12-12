import React, { useState, useEffect, useRef } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import * as d3 from 'd3';
import { Box, FormControl, InputLabel, Select, MenuItem, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, FormControlLabel, Checkbox, Typography } from '@mui/material';
import api from '../../utils/ApiFlowCytometry';
import * as XLSX from 'xlsx';
import { Download } from '@mui/icons-material';

// Add a new Histogram component
const Histogram = ({ 
  data, 
  column, 
  width = 300, 
  height = 150, 
  margin = { top: 20, right: 20, bottom: 50, left: 50 },
  applyTransform = false,
  transformParams = {} 
}) => {
  const svgRef = useRef(null);

  // Reuse the biexponential transformation from the scatterplot
  const biexponentialTransform = (value, w = 0.5, d = 0.5, a = 1, b = 1, c = 1) => {
    if (value === 0) return 0;
    const normalizedValue = value / 262144;
    const threshold = w / (d * Math.log(10));
    
    if (normalizedValue < threshold) {
      return a * (normalizedValue / threshold);
    } else {
      const expValue = a * (Math.exp(b * normalizedValue) - c * Math.exp(-d * normalizedValue));
      return expValue * 262144;
    }
  };

  const transformValue = (value) => {
    if (!applyTransform) return value;
    return biexponentialTransform(
      value,
      transformParams.w,
      transformParams.d,
      transformParams.a,
      transformParams.b,
      transformParams.c
    );
  };

  useEffect(() => {
    if (!data || data.length === 0) return;

    // Clear any existing SVG content
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Prepare the data
    const transformedData = data.map(d => transformValue(+d[column])).filter(d => !isNaN(d));

    // Create scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(transformedData))
      .range([margin.left, width - margin.right]);

    const bins = d3.histogram()
      .domain(xScale.domain())
      .thresholds(30)(transformedData);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(bins, d => d.length)])
      .range([height - margin.bottom, margin.top]);

    // Create histogram bars
    svg.append('g')
      .selectAll('rect')
      .data(bins)
      .enter()
      .append('rect')
      .attr('x', d => xScale(d.x0))
      .attr('y', d => yScale(d.length))
      .attr('width', d => Math.max(0, xScale(d.x1) - xScale(d.x0) - 1))
      .attr('height', d => height - margin.bottom - yScale(d.length))
      .attr('fill', 'steelblue')
      .attr('opacity', 0.7);

    // Create the axes
    const xAxis = d3.axisBottom(xScale).tickFormat(d3.format('.2s'));
    const yAxis = d3.axisLeft(yScale).tickFormat(d3.format('.2s'));

    // Append the axes to the SVG
    svg.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0, ${height})`) // Adjust as needed
        .call(xAxis)
        .selectAll("text") // Select the text elements of the x-axis
        .style("font-size", "12px"); // Set the desired font size

    svg.append("g")
        .attr("class", "y-axis")
        .call(yAxis)
        .selectAll("text") // Select the text elements of the y-axis
        .style("font-size", "12px"); // Set the desired font size

    // Add labels
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height)
      .attr('text-anchor', 'middle')
      .text(column);

    svg.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', 10)
      .attr('text-anchor', 'middle')
      .text('Frequency');

  }, [data, column, applyTransform, transformParams]);

  return (
    <svg 
      ref={svgRef} 
      width={width} 
      height={height}
    />
  );
};

const FlowCytometryScatterPlot = ({ data, statistics }) => {
  const {progressiveId, projectId, gatingStrategyId} = useParams();
  console.log(statistics)
  const location = useLocation();
  
  // Get parentId from URL query parameters
  const queryParams = new URLSearchParams(location.search);
  const parentId = queryParams.get('parentId');

  const columns = data.length > 0 ? Object.keys(data[0]) : [];
  const [xColumn, setXColumn] = useState(columns[0] || 'parameter1');
  const [yColumn, setYColumn] = useState(columns[1] || 'parameter2');
  const [isDrawing, setIsDrawing] = useState(false);
  const [points, setPoints] = useState([]);
  const [gateFinished, setGateFinished] = useState(false);
  const [scales, setScales] = useState({ xScale: null, yScale: null });
  const [gateName, setGateName] = useState('');
  const svgRef = useRef();
  const [showTransformSettings, setShowTransformSettings] = useState(false);

  // Update the transformation parameters state
  const [transformParams, setTransformParams] = useState({
    x: {
      type: 'biexponential', // or 'log'
      biex: {
        negative: 0,
        width: -10,
        positive: 4.5,
        max_value: 262144.000029
      },
      log: {
        offset: 1,
        decades: 4.5
      }
    },
    y: {
      type: 'biexponential', // or 'log'
      biex: {
        negative: 0,
        width: -10,
        positive: 4.5,
        max_value: 262144.000029
      },
      log: {
        offset: 1,
        decades: 4.5
      }
    }
  });

  // Separate transform flags for x and y channels
  const [channelTransforms, setChannelTransforms] = useState({
    x: false,
    y: false
  });

  // Function to create smooth colormap (blue -> green -> yellow -> red)
  const interpolateJet = (t) => {
    let r, g, b;

    if (t < 0.25) {
      // Blue to Green (0 to 0.25)
      const x = t * 4;
      r = 0;
      g = x;
      b = 1;
    } else if (t < 0.5) {
      // Green to Yellow (0.25 to 0.5)
      const x = (t - 0.25) * 4;
      r = x;
      g = 1;
      b = 1 - x;
    } else if (t < 0.75) {
      // Yellow to Orange (0.5 to 0.75)
      const x = (t - 0.5) * 4;
      r = 1;
      g = 1 - x * 0.5;
      b = 0;
    } else {
      // Orange to Red (0.75 to 1)
      const x = (t - 0.75) * 4;
      r = 1;
      g = 0.5 - x * 0.5;
      b = 0;
    }

    return d3.rgb(
      Math.round(r * 255),
      Math.round(g * 255),
      Math.round(b * 255)
    );
  };

  // Comprehensive FlowJo-style Biexponential Transformation
  const biexponentialTransform = (value, params = {}) => {
    // Default FlowJo-like parameters
    const {
      negative = 0,     // Negative decades
      width = -10,      // Width basis
      positive = 4.5,   // Positive decades
      maxValue = 262144 // Maximum data value
    } = params;

    // Prevent log(0)
    if (value <= 0) return 0;

    // Normalize value
    const x = value/maxValue;

    // Calculate key transformation parameters
    const decades = positive;
    const logDecades = Math.log(decades);
    const w = width < 0 ? 0.5 : width;
    const t = maxValue;

    // Core transformation logic
    const b = logDecades / (decades) + w;
    const a = t / (Math.exp(b * decades) - 1);
    
    // Transformation calculation
    const transformed = a * Math.exp(b * x) - a + x;

    
    return transformed * w;
  };

  // Logarithmic Transformation
  const logTransform = (value, params = {}) => {
    const {
      offset = 1,
      decades = 4.5,
      maxValue = 262144
    } = params;

    // Prevent log(0)
    const adjustedValue = Math.max(value, offset);
    
    // Standard log transformation
    return Math.log10(adjustedValue) * (maxValue / decades);
  };

  // Updated transformation function
  const transformValue = (value, column, transformParams) => {
    // Determine which channel's parameters to use
    const channelParams = column === xColumn 
      ? transformParams.x 
      : transformParams.y;

    // Check if transformation is applied
    if (!channelTransforms[column === xColumn ? 'x' : 'y']) {
      return value;
    }

    // Apply appropriate transformation
    switch(channelParams.type) {
      case 'biexponential':
        return biexponentialTransform(value, channelParams.biex);
      case 'log':
        return logTransform(value, channelParams.log);
      default:
        return value;
    }
  };

  // Add a debug function to test the transformation
  const testTransformation = () => {
    const testValues = [0, 10, 100, 1000, 10000, 100000, 262144];
    console.log("Testing transformation with current parameters:");
    testValues.forEach(v => {
      const transformed = transformValue(v, xColumn, transformParams);
      console.log(`Input: ${v}, Transformed: ${transformed}`);
    });
  };

  // Effect for drawing the scatter plot
  useEffect(() => {
    if (!Array.isArray(data) || data.length === 0) return;

    const margin = { top: 20, right: 30, bottom: 80, left: 80 };
    const width = 700 - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom;

    // Transform the data conditionally for each channel
    const rawData = data
      .map(d => ({
        x: transformValue(+d[xColumn], xColumn, transformParams),
        y: transformValue(+d[yColumn], yColumn, transformParams),
        originalX: +d[xColumn],
        originalY: +d[yColumn]
      }))
      .filter(d => !isNaN(d.x) && !isNaN(d.y));

    if (rawData.length === 0) {
      console.warn('No valid data points.');
      return;
    }

    // Linear scales for x and y
    const xScale = d3.scaleLinear()
      .domain(d3.extent(rawData, d => d.x))
      .range([0, width]);
    
    const yScale = d3.scaleLinear()
      .domain(d3.extent(rawData, d => d.y))
      .range([height, 0]);

    setScales({ xScale, yScale });

    // Create a more efficient density estimation using a grid approach
    const gridSize = 50;  // Adjust this value for performance/accuracy trade-off
    const densityGrid = new Array(gridSize).fill(0)
      .map(() => new Array(gridSize).fill(0));

    // Count points in each grid cell
    rawData.forEach(d => {
      const xBin = Math.floor((xScale(d.x) / width) * (gridSize - 1));
      const yBin = Math.floor((yScale(d.y) / height) * (gridSize - 1));
      if (xBin >= 0 && xBin < gridSize && yBin >= 0 && yBin < gridSize) {
        densityGrid[yBin][xBin]++;
      }
    });

    // Smooth the density grid using a simple box blur
    const smoothedGrid = densityGrid.map(row => [...row]);
    for (let y = 1; y < gridSize - 1; y++) {
      for (let x = 1; x < gridSize - 1; x++) {
        smoothedGrid[y][x] = (
          densityGrid[y-1][x] + densityGrid[y+1][x] +
          densityGrid[y][x-1] + densityGrid[y][x+1] +
          densityGrid[y][x]
        ) / 5;
      }
    }

    // Find max density for normalization
    const maxDensity = Math.max(...smoothedGrid.flat());

    // Function to get interpolated density at any point
    const getDensityAtPoint = (x, y) => {
      const xBin = Math.floor((x / width) * (gridSize - 1));
      const yBin = Math.floor((y / height) * (gridSize - 1));
      if (xBin >= 0 && xBin < gridSize && yBin >= 0 && yBin < gridSize) {
        return smoothedGrid[yBin][xBin] / maxDensity;
      }
      return 0;
    };

    // Clear and set up SVG
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('class', 'main-group')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const scatterGroup = svg.append('g').attr('class', 'scatter-group');

    // Draw points with density-based coloring
    scatterGroup.selectAll('circle')
      .data(rawData)
      .enter()
      .append('circle')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', 0.5) // add a definition about the point dimension --> the user must decide the dot dimension inside the plot
      .attr('fill', d => {
        const density = getDensityAtPoint(xScale(d.x), yScale(d.y));
        return interpolateJet(density);
      })
      .attr('opacity', 0.7);

    // Create and append axes (only once)
    const formatAxis = d3.format(".2s");
    const xAxis = d3.axisBottom(xScale).tickFormat(formatAxis);
    const yAxis = d3.axisLeft(yScale).tickFormat(formatAxis);

    // Append the axes to the SVG
    scatterGroup.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(xAxis)
      .selectAll("text")
      .style("font-size", "12px");

    scatterGroup.append('g')
      .call(yAxis)
      .selectAll("text")
      .style("font-size", "12px");

    // Add axis labels
    scatterGroup.append('text')
      .attr('x', width / 2)
      .attr('y', height + 60)
      .attr('fill', 'black')
      .style('text-anchor', 'middle')
      .style('font-size', '20px')
      .text(xColumn);

    scatterGroup.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -60)
      .attr('fill', 'black')
      .style("font-size", "20px")
      .style('text-anchor', 'middle')
      .text(yColumn);

    // Create gate group
    svg.append('g').attr('class', 'gate-group');

    setPoints([]);
    setGateFinished(false);
    setGateName('');

  }, [data, xColumn, yColumn, transformParams, channelTransforms]);

  // Effect for drawing the gate
  useEffect(() => {
    if (!scales.xScale || !scales.yScale) return;

    const gateGroup = d3.select(svgRef.current)
      .select('.main-group')
      .select('.gate-group');

    gateGroup.selectAll('*').remove();

    gateGroup.selectAll('.drawn-circle')
      .data(points)
      .join('circle')
      .attr('class', 'drawn-circle')
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .attr('r', 7)
      .attr('fill', 'red')
      .attr('opacity', 0.8);

    if (points.length > 1) {
      let polygonPoints = points;
      if (gateFinished) {
        polygonPoints = [...points, points[0]];
      }

      const lineGenerator = d3.line()
        .x(d => d.x)
        .y(d => d.y);

      gateGroup.selectAll('.gate-line')
        .data([polygonPoints])
        .join('path')
        .attr('class', 'gate-line')
        .attr('d', lineGenerator)
        .attr('fill', 'none')
        .attr('stroke', 'red')
        .attr('stroke-width', 2);
    }
  }, [points, scales, gateFinished]);

  const handleClick = (event) => {
    if (!isDrawing || gateFinished || !scales.xScale || !scales.yScale) return;

    const mainGroupElem = svgRef.current.querySelector('.main-group');
    const [mouseX, mouseY] = d3.pointer(event, mainGroupElem);

    // Convert pixel coordinates back to data values
    const dataX = scales.xScale.invert(mouseX);
    const dataY = scales.yScale.invert(mouseY);

    setPoints(prevPoints => [
      ...prevPoints,
      {
        x: mouseX,  // for drawing
        y: mouseY,
        original: {  // actual data values
          x: dataX,
          y: dataY
        }
      }
    ]);
  };

  const handleFinishGate = () => {
    if (gateName.trim() === '') {
      alert("Please provide a name for the gate.");
      return;
    }

    if (points.length < 3) {
      alert("A gate must have at least 3 points.");
      return;
    }

    setGateFinished(true);

    const gateVertices = points.map(p => ({
      x: p.original.x,
      y: p.original.y,
      transformations: {
        x: {
          type: transformParams.x.type,
          params: transformParams.x[transformParams.x.type]
        },
        y: {
          type: transformParams.y.type,
          params: transformParams.y[transformParams.y.type]
        }
      }
    }));

    const gateData = {
      name: gateName,
      vertices: gateVertices,
      columns: {
        xColumn: xColumn,
        yColumn: yColumn,
        xTransformation: {
          type: transformParams.x.type,
          params: transformParams.x[transformParams.x.type]
        },
        yTransformation: {
          type: transformParams.y.type,
          params: transformParams.y[transformParams.y.type]
        }
      },
      parentId: parentId
    };

    console.log("Gate Data:", JSON.stringify(gateData));

    const postGate = async () => {
      try {
        const response = await api.post(
          `/flow_cytometry/api/v1/project/${projectId}/flow_cytometry/${progressiveId}/gating_strategies/${gatingStrategyId}/gating_elements`, 
          gateData
        );
        window.alert("Gate created successfully");
      } catch (error) {
        console.error("Error submitting gate data:", error);
        alert(`Error submitting gate: ${error.message}`);
      }
    };

    postGate();
  };

  //---------------------------------------
  // Reset the user gate drawing
  //---------------------------------------
  const handleResetGate = () => {
    setPoints([]);
    setGateFinished(false);
    setGateName(''); // Reset gate name
  };

  // Updated TransformSettingsDialog
  const TransformSettingsDialog = () => {
    const [localParams, setLocalParams] = useState(transformParams);
    const [localTransformType, setLocalTransformType] = useState({
      x: localParams.x.type,
      y: localParams.y.type
    });

    const handleClose = () => {
      // Update both transformation type and parameters
      setTransformParams({
        ...localParams,
        x: {
          ...localParams.x,
          type: localTransformType.x
        },
        y: {
          ...localParams.y,
          type: localTransformType.y
        }
      });
      setShowTransformSettings(false);
    };

    return (
      <Dialog 
        open={showTransformSettings} 
        onClose={handleClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Channel Transformation Settings</DialogTitle>
        <DialogContent>
          {/* X Channel Transformation */}
          <Box mb={3}>
            <Typography variant="h6">{xColumn} Channel</Typography>
            <FormControl fullWidth margin="normal">
              <InputLabel>Transform Type</InputLabel>
              <Select
                value={localTransformType.x}
                onChange={(e) => setLocalTransformType(prev => ({
                  ...prev,
                  x: e.target.value
                }))}
              >
                <MenuItem value="biexponential">Biexponential</MenuItem>
                <MenuItem value="log">Logarithmic</MenuItem>
                <MenuItem value="none">None</MenuItem>
              </Select>
            </FormControl>

            {/* Biexponential Settings for X */}
            {localTransformType.x === 'biexponential' && (
              <Box>
                <TextField
                  label="Negative Decades"
                  type="number"
                  value={localParams.x.biex.negative}
                  onChange={(e) => setLocalParams(prev => ({
                    ...prev,
                    x: {
                      ...prev.x,
                      biex: {
                        ...prev.x.biex,
                        negative: parseFloat(e.target.value)
                      }
                    }
                  }))}
                  fullWidth
                  margin="normal"
                />
                <TextField
                  label="Width Basis"
                  type="number"
                  value={localParams.x.biex.width}
                  onChange={(e) => setLocalParams(prev => ({
                    ...prev,
                    x: {
                      ...prev.x,
                      biex: {
                        ...prev.x.biex,
                        width: parseFloat(e.target.value)
                      }
                    }
                  }))}
                  fullWidth
                  margin="normal"
                />
              </Box>
            )}

            {/* Logarithmic Settings for X */}
            {localTransformType.x === 'log' && (
              <Box>
                <TextField
                  label="Offset"
                  type="number"
                  value={localParams.x.log.offset}
                  onChange={(e) => setLocalParams(prev => ({
                    ...prev,
                    x: {
                      ...prev.x,
                      log: {
                        ...prev.x.log,
                        offset: parseFloat(e.target.value)
                      }
                    }
                  }))}
                  fullWidth
                  margin="normal"
                />
                <TextField
                  label="Decades"
                  type="number"
                  value={localParams.x.log.decades}
                  onChange={(e) => setLocalParams(prev => ({
                    ...prev,
                    x: {
                      ...prev.x,
                      log: {
                        ...prev.x.log,
                        decades: parseFloat(e.target.value)
                      }
                    }
                  }))}
                  fullWidth
                  margin="normal"
                />
              </Box>
            )}
          </Box>

          {/* Y Channel Transformation */}
          <Box mb={3}>
            <Typography variant="h6">{yColumn} Channel</Typography>
            <FormControl fullWidth margin="normal">
              <InputLabel>Transform Type</InputLabel>
              <Select
                value={localTransformType.y}
                onChange={(e) => setLocalTransformType(prev => ({
                  ...prev,
                  y: e.target.value
                }))}
              >
                <MenuItem value="biexponential">Biexponential</MenuItem>
                <MenuItem value="log">Logarithmic</MenuItem>
                <MenuItem value="none">None</MenuItem>
              </Select>
            </FormControl>

            {/* Biexponential Settings for Y */}
            {localTransformType.y === 'biexponential' && (
              <Box>
                <TextField
                  label="Negative Decades"
                  type="number"
                  value={localParams.y.biex.negative}
                  onChange={(e) => setLocalParams(prev => ({
                    ...prev,
                    y: {
                      ...prev.y,
                      biex: {
                        ...prev.y.biex,
                        negative: parseFloat(e.target.value)
                      }
                    }
                  }))}
                  fullWidth
                  margin="normal"
                />
                <TextField
                  label="Width Basis"
                  type="number"
                  value={localParams.y.biex.width}
                  onChange={(e) => setLocalParams(prev => ({
                    ...prev,
                    y: {
                      ...prev.y,
                      biex: {
                        ...prev.y.biex,
                        width: parseFloat(e.target.value)
                      }
                    }
                  }))}
                  fullWidth
                  margin="normal"
                />
              </Box>
            )}

            {/* Logarithmic Settings for Y */}
            {localTransformType.y === 'log' && (
              <Box>
                <TextField
                  label="Offset"
                  type="number"
                  value={localParams.y.log.offset}
                  onChange={(e) => setLocalParams(prev => ({
                    ...prev,
                    y: {
                      ...prev.y,
                      log: {
                        ...prev.y.log,
                        offset: parseFloat(e.target.value)
                      }
                    }
                  }))}
                  fullWidth
                  margin="normal"
                />
                <TextField
                  label="Decades"
                  type="number"
                  value={localParams.y.log.decades}
                  onChange={(e) => setLocalParams(prev => ({
                    ...prev,
                    y: {
                      ...prev.y,
                      log: {
                        ...prev.y.log,
                        decades: parseFloat(e.target.value)
                      }
                    }
                  }))}
                  fullWidth
                  margin="normal"
                />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTransformSettings(false)}>Cancel</Button>
          <Button onClick={handleClose} color="primary">Apply</Button>
        </DialogActions>
      </Dialog>
    );
  };

  // Function to download statistics data as an Excel file
  const downloadStatistics = () => {
    if (!statistics || statistics.length === 0) {
      console.error('No statistics data available');
      return;
    }

    // Create worksheet data array starting with headers
    const headers = Object.keys(statistics[0]);
    const wsData = [
      ['Statistic Type', ...headers], // First row with headers
      ['Mean', ...headers.map(header => statistics[0][header])],
      ['Standard Deviation', ...headers.map(header => statistics[1][header])],
      ['Median', ...headers.map(header => statistics[2][header])]
    ];

    // Create a new workbook and worksheet
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(wsData);

    // Add the worksheet to the workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Statistics');

    // Set column widths
    const colWidths = headers.map(() => ({ wch: 15 }));
    colWidths[0] = { wch: 20 }; // Make the first column wider for statistic names
    ws['!cols'] = colWidths;

    // Generate the Excel file
    XLSX.writeFile(wb, 'flow_cytometry_statistics.xlsx');
  };

  return (
    <div>
      <Box marginBottom={2} display="flex" flexWrap="wrap" gap={2}>
        {/* Axis Selection */}
        <Box minWidth={120}>
          <FormControl variant="outlined" size="small" fullWidth>
            <InputLabel id="x-axis-label">X-Axis</InputLabel>
            <Select
              labelId="x-axis-label"
              value={xColumn}
              onChange={(e) => setXColumn(e.target.value)}
              label="X-Axis"
            >
              {columns.map(col => (
                <MenuItem key={col} value={col}>{col}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        <Box minWidth={120}>
          <FormControl variant="outlined" size="small" fullWidth>
            <InputLabel id="y-axis-label">Y-Axis</InputLabel>
            <Select
              labelId="y-axis-label"
              value={yColumn}
              onChange={(e) => setYColumn(e.target.value)}
              label="Y-Axis"
            >
              {columns.map(col => (
                <MenuItem key={col} value={col}>{col}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        <Box>
          <Button 
            variant="contained" 
            onClick={() => setIsDrawing(!isDrawing)}
          >
            {isDrawing ? 'Stop Drawing' : 'Draw Gate'}
          </Button>
        </Box>
        {isDrawing && (
          <Box minWidth={200}>
            {/* Gate Name Input */}
            <TextField
              label="Gate Name"
              variant="outlined"
              size="small"
              value={gateName}
              onChange={(e) => {
                // Replace spaces with underscores and allow only letters, numbers, and underscores
                const sanitizedValue = e.target.value.replace(/ /g, '_').replace(/[^a-zA-Z0-9_]/g, '');
                setGateName(sanitizedValue);
              }}
              required
              fullWidth
              helperText="Only letters, numbers, and underscores allowed"
              error={gateName.includes(' ')}
            />
          </Box>
        )}
        {isDrawing && (
          <Box>
            <Button variant="contained" color="primary" onClick={handleFinishGate}>
              Finish & Export Gate
            </Button>
          </Box>
        )}
        {points.length > 0 && (
          <Box>
            <Button variant="outlined" color="secondary" onClick={handleResetGate}>
              Reset Gate
            </Button>
          </Box>
        )}
        <Box display="flex" alignItems="center" gap={2}>
          <FormControlLabel
            control={
              <Checkbox
                checked={channelTransforms.x}
                onChange={(e) => setChannelTransforms(prev => ({
                  ...prev,
                  x: e.target.checked
                }))}
              />
            }
            label={`Transform ${xColumn}`}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={channelTransforms.y}
                onChange={(e) => setChannelTransforms(prev => ({
                  ...prev,
                  y: e.target.checked
                }))}
              />
            }
            label={`Transform ${yColumn}`}
          />
          <Button 
            variant="outlined"
            onClick={() => setShowTransformSettings(true)}
          >
            Modify Transformation Parameters
          </Button>
        </Box>
        <Box>
          <Button 
            variant="outlined" 
            onClick={testTransformation}
            style={{ marginLeft: '10px' }}
          >
            Test Transformation
          </Button>
        </Box>
        <Box>
          <Button 
            variant="outlined" 
            onClick={downloadStatistics}
            startIcon={<Download />}
            disabled={!statistics || statistics.length === 0}
          >
            Download Statistics
          </Button>
        </Box>
      </Box>

      {/* Render the settings dialog */}
      <TransformSettingsDialog />

      {/* The SVG scatter plot and gate drawing */}
      <Box display="flex" flexDirection="column">
        {/* Scatterplot and Histograms Container */}
        <Box display="flex" alignItems="center" justifyContent="center">
          {/* Scatterplot */}
          <svg 
            ref={svgRef} 
            onClick={handleClick} 
            style={{ border: '1px solid black', width: '700px', height: '500px' }} 
          />
        </Box>
      </Box>
    </div>
  );
};

export default FlowCytometryScatterPlot;