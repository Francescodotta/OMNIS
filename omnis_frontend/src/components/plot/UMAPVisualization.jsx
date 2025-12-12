import React, { useState } from "react";
import Plot from "react-plotly.js";
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  Tooltip,
} from "@mui/material";
import LensIcon from "@mui/icons-material/Lens";

const UMAPVisualization = ({ data }) => {
  // Dynamically extract all column names from the data
  const allColumns = Object.keys(data[0]); // Get all keys from the first object
  const excludedColumns = ["UMAP1", "UMAP2"]; // Columns to exclude
  const colorableColumns = allColumns.filter((col) => !excludedColumns.includes(col)); // Columns available for coloring

  // State to control the coloring attribute and mode (continuous/categorical)
  const [colorBy, setColorBy] = useState(colorableColumns[0]); // Default to the first colorable column
  const [isCategorical, setIsCategorical] = useState(false); // Default to continuous mode
  const [highlightedCategory, setHighlightedCategory] = useState(null); // State for the selected category (single click)
  const [isolatedCategory, setIsolatedCategory] = useState(null); // State for isolated category (double click)
  const [vmin, setVmin] = useState(null); // Minimum value for continuous variables
  const [vmax, setVmax] = useState(null); // Maximum value for continuous variables

  // Extract UMAP coordinates
  const umapX = data.map((item) => item.UMAP1);
  const umapY = data.map((item) => item.UMAP2);

  // Dynamically set the color based on the selected attribute and mode
  let colorMap;
  let markerColorscale = "Viridis"; // Default colorscale for continuous variables
  let markerShowscale = true; // Default: show color scale
  let legendItems = []; // Legend items for categorical variables

  if (isCategorical) {
    // Custom colors for categorical variables
    const uniqueCategories = [...new Set(data.map((item) => item[colorBy]))];
    const categoryColors = uniqueCategories.map((_, index) =>
      `hsl(${(index * 360) / uniqueCategories.length}, 70%, 50%)`
    );
    const categoryColorMap = Object.fromEntries(
      uniqueCategories.map((category, index) => [category, categoryColors[index]])
    );
    colorMap = data.map((item) => categoryColorMap[item[colorBy]]);
    markerColorscale = null; // Disable colorscale
    markerShowscale = false; // Hide color scale

    // Create legend items
    legendItems = uniqueCategories.map((category, index) => ({
      name: category,
      color: categoryColors[index],
    }));
  } else {
    // Default behavior for continuous variables
    const values = data.map((item) => item[colorBy]);
    const minVal = vmin !== null ? vmin : Math.min(...values);
    const maxVal = vmax !== null ? vmax : Math.max(...values);
    colorMap = values.map((val) =>
      val < minVal ? minVal : val > maxVal ? maxVal : val
    ); // Clamp values to vmin and vmax
  }

  // Generate hover text dynamically based on all columns
  const hoverText = data.map((item) =>
    allColumns
      .map((col) => `${col}: ${item[col]}`)
      .join("<br>")
  );

  // Handle single click on legend item
  const handleLegendClick = (categoryName) => {
    if (highlightedCategory === categoryName) {
      setHighlightedCategory(null); // Deselect if already selected
    } else {
      setHighlightedCategory(categoryName);
      setIsolatedCategory(null); // Reset isolated category
    }
  };

  // Handle double click on legend item
  const handleLegendDoubleClick = (categoryName) => {
    if (isolatedCategory === categoryName) {
      setIsolatedCategory(null); // Show all if already isolated
      setHighlightedCategory(null);
    } else {
      setIsolatedCategory(categoryName); // Isolate this category
      setHighlightedCategory(null);
    }
  };

  // Generate plot data for categorical variables
  const generateCategoricalPlotData = () => {
    return legendItems.map((item) => {
      const indices = data
        .map((d, i) => (d[colorBy] === item.name ? i : -1))
        .filter((i) => i !== -1);

      // Determine visibility and opacity
      let visible = true;
      let opacity = 1;

      if (isolatedCategory !== null) {
        // If a category is isolated, hide others
        visible = item.name === isolatedCategory;
        opacity = 1;
      } else if (highlightedCategory !== null) {
        // If a category is highlighted, make others transparent
        opacity = item.name === highlightedCategory ? 1 : 0.15;
      }

      return {
        x: indices.map((i) => umapX[i]),
        y: indices.map((i) => umapY[i]),
        text: indices.map((i) => hoverText[i]),
        mode: "markers",
        marker: {
          size: 5,
          color: item.color,
          opacity: opacity,
        },
        name: item.name,
        showlegend: false, // Disable Plotly's internal legend
        visible: visible,
        hoverinfo: "text",
      };
    });
  };

  // Generate plot data for continuous variables
  const generateContinuousPlotData = () => {
    return [
      {
        x: umapX,
        y: umapY,
        text: hoverText,
        mode: "markers",
        marker: {
          size: 5,
          color: colorMap,
          colorscale: markerColorscale,
          showscale: markerShowscale,
          colorbar: {
            title: colorBy,
            thickness: 15,
            len: 0.5,
            x: 1.02,
          },
        },
        hoverinfo: "text",
        showlegend: false,
      },
    ];
  };

  return (
    <Card elevation={2} sx={{ borderRadius: 2, overflow: "hidden" }}>
      <CardHeader
        title={
          <Typography variant="h6" sx={{ fontWeight: "bold" }}>
            UMAP Visualization
          </Typography>
        }
        sx={{
          bgcolor: "primary.main",
          color: "primary.contrastText",
          py: 1.5,
        }}
      />

      <CardContent>
        {/* Controls */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 3 }}>
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              select
              label="Color by"
              value={colorBy}
              onChange={(e) => {
                setColorBy(e.target.value);
                setHighlightedCategory(null);
                setIsolatedCategory(null);
                setVmin(null);
                setVmax(null);
              }}
              SelectProps={{
                native: true,
              }}
              fullWidth
            >
              {colorableColumns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </TextField>

            <Button
              variant="contained"
              onClick={() => {
                setIsCategorical(!isCategorical);
                setHighlightedCategory(null);
                setIsolatedCategory(null);
              }}
              sx={{
                bgcolor: isCategorical ? "secondary.main" : "primary.main",
                color: "white",
                minWidth: 120,
              }}
            >
              {isCategorical ? "Categorical" : "Continuous"}
            </Button>
          </Box>

          {!isCategorical && (
            <Box sx={{ display: "flex", gap: 2 }}>
              <TextField
                label="Min"
                type="number"
                value={vmin !== null ? vmin : ""}
                onChange={(e) =>
                  setVmin(e.target.value !== "" ? parseFloat(e.target.value) : null)
                }
                fullWidth
              />
              <TextField
                label="Max"
                type="number"
                value={vmax !== null ? vmax : ""}
                onChange={(e) =>
                  setVmax(e.target.value !== "" ? parseFloat(e.target.value) : null)
                }
                fullWidth
              />
            </Box>
          )}
        </Box>

        {/* UMAP Plot */}
        <Plot
          data={isCategorical ? generateCategoricalPlotData() : generateContinuousPlotData()}
          layout={{
            title: "",
            xaxis: {
              title: "UMAP 1",
              zeroline: false,
            },
            yaxis: {
              title: "UMAP 2",
              zeroline: false,
            },
            hovermode: "closest",
            showlegend: false, // Disable Plotly's internal legend
            autosize: true,
            height: 700,
            margin: {
              l: 50,
              r: 50,
              t: 30,
              b: 50,
            },
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ["lasso2d", "select2d"],
          }}
          style={{ width: "100%", height: "100%" }}
        />

        {/* Custom Legend for categorical variables */}
        {isCategorical && (
          <Paper elevation={1} sx={{ mt: 3, p: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                Legend
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Click: highlight | Double-click: isolate
              </Typography>
            </Box>
            <Grid container spacing={1}>
              {legendItems.map((item) => (
                <Grid
                  item
                  xs={6}
                  sm={4}
                  md={3}
                  lg={2}
                  key={item.name}
                >
                  <Tooltip title={`Click to highlight, double-click to isolate "${item.name}"`}>
                    <Paper
                      elevation={
                        highlightedCategory === item.name || isolatedCategory === item.name
                          ? 3
                          : 0
                      }
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        cursor: "pointer",
                        bgcolor:
                          isolatedCategory === item.name
                            ? "action.selected"
                            : highlightedCategory === item.name
                            ? "action.hover"
                            : "inherit",
                        p: 1,
                        borderRadius: 1,
                        border:
                          isolatedCategory === item.name
                            ? "2px solid"
                            : highlightedCategory === item.name
                            ? "1px solid"
                            : "1px solid transparent",
                        borderColor:
                          isolatedCategory === item.name || highlightedCategory === item.name
                            ? item.color
                            : "transparent",
                        opacity:
                          isolatedCategory !== null && isolatedCategory !== item.name
                            ? 0.5
                            : 1,
                        transition: "all 0.2s ease-in-out",
                        "&:hover": {
                          bgcolor: "action.hover",
                        },
                      }}
                      onClick={() => handleLegendClick(item.name)}
                      onDoubleClick={() => handleLegendDoubleClick(item.name)}
                    >
                      <LensIcon sx={{ color: item.color, mr: 1, fontSize: 16 }} />
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight:
                            highlightedCategory === item.name || isolatedCategory === item.name
                              ? "bold"
                              : "normal",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {item.name}
                      </Typography>
                    </Paper>
                  </Tooltip>
                </Grid>
              ))}
            </Grid>

            {/* Reset button */}
            {(highlightedCategory !== null || isolatedCategory !== null) && (
              <Box sx={{ mt: 2, display: "flex", justifyContent: "flex-end" }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    setHighlightedCategory(null);
                    setIsolatedCategory(null);
                  }}
                >
                  Reset Selection
                </Button>
              </Box>
            )}
          </Paper>
        )}
      </CardContent>
    </Card>
  );
};

export default UMAPVisualization;