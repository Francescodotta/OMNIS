import React, { useState, useMemo } from "react";
import Plot from "react-plotly.js";
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from "@mui/material";

const HeatmapVisualization = ({ data }) => {
  // Dynamically extract column names
  const allColumns = Object.keys(data[0]);
  const excludedFromMarkers = ["UMAP1", "UMAP2", "file_id", "group"]; // Exclude these from markers

  // Separate continuous (markers) and categorical variables
  const continuousColumns = allColumns.filter(
    (col) => !excludedFromMarkers.includes(col) && typeof data[0][col] === "number"
  );

  // Include "file_id" and "group" explicitly as categorical columns for grouping
  const forcedCategoricalColumns = ["file_id", "group"];
  const categoricalColumns = [
    ...new Set(
      allColumns
        .filter((col) => typeof data[0][col] !== "number")
        .concat(forcedCategoricalColumns)
    ),
  ];

  // State for heatmap options
  const [groupBy, setGroupBy] = useState(categoricalColumns[0] || "");
  const [normalizeRows, setNormalizeRows] = useState(true);
  const [colorscale, setColorscale] = useState("Cool");
  const [sortBy, setSortBy] = useState(continuousColumns[0] || "");
  const [thresholdMethod, setThresholdMethod] = useState("mean");

  // Helper function to calculate median
  const calculateMedian = (values) => {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0
      ? sorted[mid]
      : (sorted[mid - 1] + sorted[mid]) / 2;
  };

  // Calculate aggregated data for heatmap
  const heatmapData = useMemo(() => {
    if (!groupBy) return null;

    // Get unique categories
    const uniqueCategories = [...new Set(data.map((item) => item[groupBy]))];
    const totalPoints = data.length;

    // Calculate thresholds for each marker
    const thresholds = continuousColumns.map((marker) => {
      const values = data.map((item) => item[marker]);
      return thresholdMethod === "mean"
        ? values.reduce((a, b) => a + b, 0) / values.length
        : calculateMedian(values);
    });

    // Calculate mean values for each marker per category
    const aggregatedData = uniqueCategories.map((category) => {
      const categoryData = data.filter((item) => item[groupBy] === category);
      const totalPointsInGroup = categoryData.length;

      const means = continuousColumns.map((marker) => {
        const values = categoryData.map((item) => item[marker]);
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        return mean;
      });

      const aboveThreshold = continuousColumns.map((marker, index) => {
        const values = categoryData.map((item) => item[marker]);
        const countAboveThreshold = values.filter(
          (val) => val > thresholds[index]
        ).length;
        return {
          count: countAboveThreshold,
          percentageOfGroup: (countAboveThreshold / totalPointsInGroup) * 100,
          percentageOfTotal: (countAboveThreshold / totalPoints) * 100,
        };
      });

      return {
        category,
        means,
        totalPointsInGroup,
        aboveThreshold,
      };
    });

    // Sort rows based on the selected column
    if (sortBy) {
      const columnIndex = continuousColumns.indexOf(sortBy);
      aggregatedData.sort((a, b) => b.means[columnIndex] - a.means[columnIndex]);
    }

    // Create z-values matrix
    let zValues = aggregatedData.map((item) => item.means);

    // Normalize rows (z-score) if enabled
    if (normalizeRows) {
      zValues = zValues.map((row) => {
        const mean = row.reduce((a, b) => a + b, 0) / row.length;
        const std = Math.sqrt(
          row.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / row.length
        );
        return row.map((val) => (std !== 0 ? (val - mean) / std : 0));
      });
    }

    return {
      z: zValues,
      x: continuousColumns,
      y: aggregatedData.map((item) => String(item.category)),
      aggregatedData,
      thresholds,
    };
  }, [data, groupBy, continuousColumns, normalizeRows, sortBy, thresholdMethod]);

  // Available colorscales
  const colorscales = [
    "RdBu",
    "Viridis",
    "Plasma",
    "Inferno",
    "Magma",
    "Hot",
    "Cool",
    "Picnic",
    "Portland",
    "Jet",
    "Greys",
    "YlGnBu",
    "YlOrRd",
  ];

  if (!heatmapData) {
    return (
      <Card elevation={2} sx={{ borderRadius: 2, overflow: "hidden" }}>
        <CardContent>
          <Typography>No categorical variables available for grouping.</Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card elevation={2} sx={{ borderRadius: 2, overflow: "hidden" }}>
      <CardHeader
        title={
          <Typography variant="h6" sx={{ fontWeight: "bold" }}>
            Heatmap Visualization
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
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 3 }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Group by</InputLabel>
            <Select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              label="Group by"
            >
              {categoricalColumns.map((col) => (
                <MenuItem key={col} value={col}>
                  {col}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Sort by</InputLabel>
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              label="Sort by"
            >
              {continuousColumns.map((col) => (
                <MenuItem key={col} value={col}>
                  {col}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Threshold Method</InputLabel>
            <Select
              value={thresholdMethod}
              onChange={(e) => setThresholdMethod(e.target.value)}
              label="Threshold Method"
            >
              <MenuItem value="mean">Mean</MenuItem>
              <MenuItem value="median">Median</MenuItem>
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Colorscale</InputLabel>
            <Select
              value={colorscale}
              onChange={(e) => setColorscale(e.target.value)}
              label="Colorscale"
            >
              {colorscales.map((cs) => (
                <MenuItem key={cs} value={cs}>
                  {cs}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Switch
                checked={normalizeRows}
                onChange={(e) => setNormalizeRows(e.target.checked)}
              />
            }
            label="Normalize rows (Z-score)"
          />
        </Box>

        {/* Heatmap Plot */}
        <Plot
          data={[
            {
              type: "heatmap",
              z: heatmapData.z,
              x: heatmapData.x,
              y: heatmapData.y,
              colorscale: colorscale,
              reversescale: colorscale === "RdBu",
              colorbar: {
                title: normalizeRows ? "Z-score" : "Mean Expression",
                thickness: 15,
                len: 0.9,
              },
              hoverongaps: false,
              hovertemplate:
                "<b>%{y}</b><br>" +
                "Marker: %{x}<br>" +
                "Value: %{z:.3f}<extra></extra>",
            },
          ]}
          layout={{
            title: "",
            xaxis: {
              title: "Markers",
              tickangle: -45,
              tickfont: { size: 10 },
            },
            yaxis: {
              title: groupBy,
              tickfont: { size: 12 },
            },
            autosize: true,
            height: 600 + heatmapData.y.length * 30,
            margin: {
              l: 150,
              r: 80,
              t: 30,
              b: 150,
            },
          }}
          config={{
            responsive: true,
            displayModeBar: true,
          }}
          style={{ width: "80%", height: "100%" }}
        />

        {/* Threshold Statistics */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Threshold Analysis
          </Typography>
          {heatmapData.aggregatedData.map((item, index) => (
            <Box key={index} sx={{ mb: 2 }}>
              <Typography variant="subtitle1">
                <b>{item.category}:</b>
              </Typography>
              {item.aboveThreshold.map((marker, markerIndex) => (
                <Typography key={markerIndex} variant="body2">
                  Marker <b>{continuousColumns[markerIndex]}</b>: {marker.count} points above
                  threshold ({marker.percentageOfGroup.toFixed(2)}% of group,{" "}
                  {marker.percentageOfTotal.toFixed(2)}% of total)
                </Typography>
              ))}
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default HeatmapVisualization;