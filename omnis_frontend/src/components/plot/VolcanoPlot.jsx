import React from "react";
import Plot from "react-plotly.js";
import { Card, CardHeader, CardContent, Typography } from "@mui/material";

const VolcanoPlot = ({ data, imageUrl }) => {
  if (!data && !imageUrl) return <Typography>No volcano data available.</Typography>;

  // If image is provided prefer to show it
  if (imageUrl) {
    return (
      <Card>
        <CardHeader title="Volcano Plot" />
        <CardContent>
          <img src={imageUrl} alt="Volcano" style={{ maxWidth: "100%" }} />
        </CardContent>
      </Card>
    );
  }

  const rows = Array.isArray(data) ? data : [];
  if (rows.length === 0) return <Typography>No volcano data available.</Typography>;

  const xKey = rows[0].log2FoldChange ?? rows[0].logFC ?? Object.keys(rows[0]).find(k => /log/i.test(k)) ;
  const pKey = rows[0].p_value ?? rows[0].pvalue ?? rows[0].p ?? Object.keys(rows[0]).find(k => /p(.?_)?value|pval|p$/i.test(k));

  if (!xKey || !pKey) return <Typography>Volcano data format not recognized.</Typography>;

  const x = rows.map(r => Number(r[xKey]));
  const y = rows.map(r => {
    const p = Number(r[pKey]);
    return Number.isFinite(p) && p > 0 ? -Math.log10(p) : 0;
  });
  const labels = rows.map(r => r.gene || r.marker || r.name || "");

  return (
    <Card>
      <CardHeader title="Volcano Plot" />
      <CardContent>
        <Plot
          data={[{
            x, y, text: labels, mode: "markers",
            marker: { size: 6, color: y, colorscale: "Viridis", showscale: true },
            hovertemplate: "%{text}<br>%{x:.3f}<br>-log10(p) %{y:.2f}<extra></extra>"
          }]}
          layout={{ height: 600, xaxis:{ title: "log2FC" }, yaxis:{ title: "-log10(p-value)" }, hovermode: "closest" }}
          config={{ responsive: true }}
          style={{ width: "100%" }}
        />
      </CardContent>
    </Card>
  );
};

export default VolcanoPlot;