import React, { useEffect, useRef, useState } from "react";
import { useParams } from 'react-router-dom';
import * as d3 from "d3";
import { fetchHeatmap } from "../../services/fcs_api"; // Import the API function
import { Box, Button, CircularProgress, Alert, FormControlLabel, Checkbox, TextField } from '@mui/material';
import Typography from '@mui/material/Typography';

const Heatmap = ({ projectId, pipelineId, width = 1500, height = 500 }) => {
  const svgRef = useRef();
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [searchTerm, setSearchTerm] = useState(''); // nuovo stato

  // filtro dinamico dei parametri
  const filteredColumns = columns.filter(col =>
    col.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const loadData = async () => {
      try {
        const heatmapData = await fetchHeatmap(projectId, pipelineId);
        console.log(heatmapData);
        const columns = Object.keys(heatmapData.data[0] || {}).filter(col => col !== 'Leiden_Cluster');
        setData(heatmapData.data.map(d => {
          const { Leiden_Cluster, ...rest } = d;
          return rest;
        }) || []);
        setColumns(columns);
        setSelectedColumns(columns);
        console.log(heatmapData);
      } catch (err) {
        setError('Failed to load heatmap data.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [projectId, pipelineId]);

  useEffect(() => {
    if (!data.length || !showHeatmap) return;

    // margini intorno al plot
    const margin = { top: 50, right: 100, bottom: 50, left: 100 };

    // altezza per ogni cluster (riga) e calcolo dinamico dell’altezza totale
    const rowHeight = 16;
    const dynamicHeight = margin.top + margin.bottom + data.length * rowHeight;

    // dimensioni delle celle
    const cellWidth  = (width  - margin.left - margin.right) / (selectedColumns.length || 1);
    const cellHeight = rowHeight;

    // settaggio width/height del SVG
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", dynamicHeight);

    svg.selectAll("*").remove();

    const colorScale = d3.scaleSequential(d3.interpolateBlues)
      .domain([
        d3.min(data.flatMap(d => selectedColumns.map(col => d[col]))),
        d3.max(data.flatMap(d => selectedColumns.map(col => d[col])))
      ]);

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    // disegno celle
    g.selectAll("rect")
      .data(data.flatMap((d, i) =>
        selectedColumns.map((col, j) => ({ value: d[col], row: i, col: j }))
      ))
      .enter().append("rect")
        .attr("x",      d => d.col * cellWidth)
        .attr("y",      d => d.row * cellHeight)
        .attr("width",  cellWidth)
        .attr("height", cellHeight)
        .attr("fill",   d => colorScale(d.value))
        .attr("stroke", "#fff")
        .on("mouseover",  function() { d3.select(this).attr("stroke", "black"); })
        .on("mouseout",   function() { d3.select(this).attr("stroke", "#fff"); });

    // etichette righe
    g.selectAll(".rowLabel")
      .data(data.map((_, i) => i))
      .enter().append("text")
        .attr("x", -10)
        .attr("y", (_, i) => i * cellHeight + cellHeight/2)
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .text(d => d)
        .style("font-size", "12px");

    // etichette colonne
    g.selectAll(".colLabel")
      .data(selectedColumns)
      .enter().append("text")
        .attr("x",      (_, i) => i * cellWidth + cellWidth/2)
        .attr("y",      -10)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .text(d => d)
        .style("font-size", "12px");

    // legenda colori
    const legendHeight = 400;
    const legendWidth  = 20;
    const legendSvg = svg.append("g")
      .attr("transform", `translate(${width - margin.right + 20}, ${margin.top})`);

    const legendScale = d3.scaleLinear()
      .domain(colorScale.domain())
      .range([legendHeight, 0]);

    const legendAxis = d3.axisRight(legendScale).ticks(5);

    const defs = svg.append("defs");
    const linearGradient = defs.append("linearGradient")
      .attr("id", "linear-gradient")
      .attr("x1", "0%").attr("y1", "100%")
      .attr("x2", "0%").attr("y2", "0%");

    linearGradient.selectAll("stop")
      .data(colorScale.ticks().map((t, i, n) => ({
        offset: `${100 * i/(n.length-1)}%`, color: colorScale(t)
      })))
      .enter().append("stop")
        .attr("offset", d => d.offset)
        .attr("stop-color", d => d.color);

    legendSvg.append("rect")
      .attr("width",  legendWidth)
      .attr("height", legendHeight)
      .style("fill", "url(#linear-gradient)");

    legendSvg.append("g")
      .attr("transform", `translate(${legendWidth},0)`)
      .call(legendAxis);

  }, [data, selectedColumns, width, showHeatmap]);

  const handleColumnToggle = (column) => {
    setSelectedColumns(prev =>
      prev.includes(column)
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  };

  const handleSelectAllToggle = () => {
    if (selectedColumns.length === columns.length) {
      setSelectedColumns([]);
    } else {
      setSelectedColumns(columns);
    }
  };

  if (loading) return <Box display="flex" justifyContent="center" alignItems="center" height="100vh"><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Box p={4}>
      <Box mb={2}>
        {/* search bar */}
        <TextField
          size="small"
          placeholder="Search parameter…"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          sx={{ mb: 2, width: 300 }}
        />

        {/* checkbox filtrate */}
        {filteredColumns.map(column => (
          <FormControlLabel
            key={column}
            control={
              <Checkbox
                checked={selectedColumns.includes(column)}
                onChange={() => handleColumnToggle(column)}
                name={column}
                color="primary"
              />
            }
            label={column}
          />
        ))}

        <Button
          variant="outlined"
          size="small"
          onClick={handleSelectAllToggle}
          sx={{ ml: 2 }}
        >
          {selectedColumns.length === columns.length ? 'Deselect All' : 'Select All'}
        </Button>
      </Box>
      <Button variant="contained" color="primary" onClick={() => setShowHeatmap(true)}>
        View Heatmap
      </Button>
      <svg ref={svgRef}></svg>
    </Box>
  );
};

export default Heatmap;