import React, { useState, useMemo } from "react";
import Plot from "react-plotly.js";
import { Card, CardHeader, CardContent, Typography, FormControl, InputLabel, Select, MenuItem, Box } from "@mui/material";

const StatHeatmap = ({ data }) => {
  const [viewMode, setViewMode] = useState("all");
  const [consistencyFilter, setConsistencyFilter] = useState("all");

  const rows = useMemo(() => {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.data)) return data.data;
    if (Array.isArray(data.rows)) return data.rows;
    return [];
  }, [data]);

  const treatmentKey = useMemo(() => {
    if (rows.length === 0) return "treatment_id";
    const treatmentKeyCandidates = ["treatment_id", "treatment", "group", "label", "comparison"];
    const allKeys = Object.keys(rows[0]);
    return allKeys.find(k => treatmentKeyCandidates.includes(k.toLowerCase())) || "treatment_id";
  }, [rows]);

  const allNumericKeys = useMemo(() => {
    if (rows.length === 0) return [];
    const allKeys = Object.keys(rows[0]);
    return allKeys.filter((k) => {
      if (k.toLowerCase() === treatmentKey.toLowerCase()) return false;
      for (let i = 0; i < rows.length; i++) {
        const v = rows[i][k];
        if (v !== undefined && v !== null && v !== "") return true;
      }
      return false;
    });
  }, [rows, treatmentKey]);

  const markerStats = useMemo(() => {
    const stats = {};
    
    allNumericKeys.forEach(marker => {
      const values = rows.map(row => {
        const v = row[marker];
        if (v === null || v === undefined) return null;
        const n = typeof v === "number" ? v : Number(v);
        return Number.isFinite(n) ? n : null;
      }).filter(v => v !== null);

      const allPositive = values.length > 0 && values.every(v => v > 0);
      const allNegative = values.length > 0 && values.every(v => v < 0);
      const hasPositive = values.some(v => v > 0);
      const hasNegative = values.some(v => v < 0);

      stats[marker] = {
        alwaysUp: allPositive,
        alwaysDown: allNegative,
        hasPositive,
        hasNegative,
        valueCount: values.length
      };
    });

    return stats;
  }, [rows, allNumericKeys]);

  const filteredMarkers = useMemo(() => {
    let filtered = [...allNumericKeys];

    if (viewMode === "upregulated") {
      filtered = filtered.filter(m => markerStats[m]?.hasPositive);
    } else if (viewMode === "downregulated") {
      filtered = filtered.filter(m => markerStats[m]?.hasNegative);
    }

    if (consistencyFilter === "always_up") {
      filtered = filtered.filter(m => markerStats[m]?.alwaysUp);
    } else if (consistencyFilter === "always_down") {
      filtered = filtered.filter(m => markerStats[m]?.alwaysDown);
    }

    return filtered;
  }, [allNumericKeys, viewMode, consistencyFilter, markerStats]);

  console.log("StatHeatmap: received data type:", typeof data, "rowsLength:", rows.length);
  if (rows.length > 0) console.log("StatHeatmap sample rows:", rows.slice(0, 2));
  console.log("StatHeatmap: chosen treatmentKey:", treatmentKey);
  console.log("StatHeatmap: markers stats", {
    total: allNumericKeys.length,
    filtered: filteredMarkers.length,
    viewMode,
    consistencyFilter,
    sampleStats: Object.fromEntries(Object.entries(markerStats).slice(0, 3))
  });

  if (!rows || rows.length === 0) {
    return <Typography>No heatmap data available.</Typography>;
  }

  if (filteredMarkers.length === 0) {
    return (
      <Card>
        <CardHeader title="Statistical Heatmap" />
        <CardContent>
          <Typography>No markers match the selected filters.</Typography>
        </CardContent>
      </Card>
    );
  }

  const yOrder = rows.map(r => String(r[treatmentKey] ?? "Unknown"));

  const z = rows.map((row) =>
    filteredMarkers.map((marker) => {
      const v = row[marker];
      if (v === null || v === undefined) return null;
      const n = typeof v === "number" ? v : Number(v);
      return Number.isFinite(n) ? n : null;
    })
  );

  let maxAbs = 0;
  for (let i = 0; i < z.length; i++) {
    for (let j = 0; j < (z[i] || []).length; j++) {
      const val = z[i][j];
      if (val != null) maxAbs = Math.max(maxAbs, Math.abs(val));
    }
  }
  if (maxAbs === 0) maxAbs = 1;

  const hover = z.map((rowZ, i) =>
    rowZ.map((val, j) => {
      const marker = filteredMarkers[j];
      const display = val == null ? "NA" : Number(val).toFixed(3);
      const stats = markerStats[marker];
      const consistency = stats.alwaysUp ? " 🔺 Always UP" : stats.alwaysDown ? " 🔻 Always DOWN" : "";
      return `<b>${yOrder[i]}</b><br>${marker}: ${display}${consistency}<extra></extra>`;
    })
  );

  const alwaysUpCount = allNumericKeys.filter(m => markerStats[m]?.alwaysUp).length;
  const alwaysDownCount = allNumericKeys.filter(m => markerStats[m]?.alwaysDown).length;

  return (
    <Card>
      <CardHeader
        title="Statistical Heatmap"
        subheader={`${filteredMarkers.length} markers × ${yOrder.length} treatments (${alwaysUpCount} always ↑, ${alwaysDownCount} always ↓)`}
      />
      <CardContent>
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>View Mode</InputLabel>
            <Select
              value={viewMode}
              label="View Mode"
              onChange={(e) => setViewMode(e.target.value)}
            >
              <MenuItem value="all">All Markers</MenuItem>
              <MenuItem value="upregulated">Upregulated Only</MenuItem>
              <MenuItem value="downregulated">Downregulated Only</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Consistency Filter</InputLabel>
            <Select
              value={consistencyFilter}
              label="Consistency Filter"
              onChange={(e) => setConsistencyFilter(e.target.value)}
            >
              <MenuItem value="all">All Consistency</MenuItem>
              <MenuItem value="always_up">Always Upregulated</MenuItem>
              <MenuItem value="always_down">Always Downregulated</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Plot
          data={[
            {
              z,
              x: filteredMarkers,
              y: yOrder,
              type: "heatmap",
              colorscale: "RdBu",
              zmid: 0,
              zmin: -maxAbs,
              zmax: maxAbs,
              hoverinfo: "text",
              text: hover,
              zauto: false,
              colorbar: {
                title: "Value",
                titleside: "right"
              }
            },
          ]}
          layout={{
            height: Math.max(400, yOrder.length * 80 + 120),
            margin: {
              l: 180,
              b: Math.min(300, filteredMarkers.length * 8),
              r: 120,
              t: 50
            },
            yaxis: {
              automargin: true,
              tickfont: { size: 12 },
              title: ""
            },
            xaxis: {
              automargin: true,
              tickangle: -45,
              tickfont: { size: 9 },
              title: "Markers"
            },
          }}
          config={{ responsive: true, displayModeBar: true }}
          style={{ width: "100%" }}
        />

        <div style={{ marginTop: '10px', fontSize: '11px', color: '#666', textAlign: 'center' }}>
          <p>
            🔴 Positive values (red) = upregulation | 🔵 Negative values (blue) = downregulation
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default StatHeatmap;