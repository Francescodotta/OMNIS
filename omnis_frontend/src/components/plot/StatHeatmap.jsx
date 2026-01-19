import React from "react";
import Plot from "react-plotly.js";
import { Card, CardHeader, CardContent, Typography } from "@mui/material";

const StatHeatmap = ({ data }) => {
  // supporta: data = [{...}, ...] oppure data = { data: [{...}, ...] } o data = { rows: [...] }
  const rows = (() => {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.data)) return data.data;
    if (Array.isArray(data.rows)) return data.rows;
    return [];
  })();

  // logging health status (use console.log per essere sicuri di vederli nella console)
  console.log("StatHeatmap: received data type:", typeof data, "rowsLength:", rows.length);
  if (rows.length > 0) console.log("StatHeatmap sample rows:", rows.slice(0, 2));

  if (!rows || rows.length === 0) return <Typography>No heatmap data available.</Typography>;

  // Exclude non-marker keys
  const excludeKeys = new Set(["Time", "time", "treatment_id", "file_id", "filename"]);
  const isUMAPKey = (k) => /umap|umap1|umap2/i.test(k);

  const allKeys = Array.from(rows.reduce((s, r) => {
    Object.keys(r).forEach(k => s.add(k));
    return s;
  }, new Set()));

  const numericKeys = allKeys.filter((k) => {
    if (excludeKeys.has(k)) return false;
    if (isUMAPKey(k)) return false;
    for (let i = 0; i < rows.length; i++) {
      const v = rows[i][k];
      if (typeof v === "number" && Number.isFinite(v)) return true;
      if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return true;
    }
    return false;
  });

  console.log("StatHeatmap: keys discovered:", { allKeysCount: allKeys.length, numericKeysCount: numericKeys.length });
  if (numericKeys.length > 0) console.log("StatHeatmap: numericKeys sample:", numericKeys.slice(0, 40));

  if (numericKeys.length === 0) {
    console.log("StatHeatmap: no numeric keys found", { allKeys, sampleRows: rows.slice(0,2) });
    return <Typography>No numeric markers found for heatmap.</Typography>;
  }

  const treatmentKeyCandidates = ["treatment_id", "treatment", "group", "label"];
  const treatmentKey = allKeys.find(k => treatmentKeyCandidates.includes(k)) || "treatment_id";

  console.log("StatHeatmap: chosen treatmentKey:", treatmentKey);

  const yOrder = [];
  const seen = new Set();
  rows.forEach(r => {
    const t = r[treatmentKey] == null ? "" : String(r[treatmentKey]);
    if (!seen.has(t)) {
      seen.add(t);
      yOrder.push(t);
    }
  });

  console.log("StatHeatmap: yOrder length:", yOrder.length, "sample:", yOrder.slice(0,10));

  // Compute z matrix: mean per marker per treatment (ignore NaN / missing)
  const z = yOrder.map((t) => {
    const groupRows = rows.filter(r => {
      const val = r[treatmentKey] == null ? "" : String(r[treatmentKey]);
      return val === t;
    });
    return numericKeys.map((k) => {
      const vals = groupRows.map(r => {
        const v = r[k];
        if (typeof v === "number") return Number.isFinite(v) ? v : null;
        if (typeof v === "string") {
          const n = v.trim() === "" ? NaN : Number(v);
          return Number.isFinite(n) ? n : null;
        }
        return null;
      }).filter(v => v !== null && !Number.isNaN(v));
      if (vals.length === 0) return null;
      const sum = vals.reduce((a,b) => a + b, 0);
      return sum / vals.length;
    });
  });

  // log z matrix size / sample
  console.log("StatHeatmap: z matrix computed", {
    zRows: z.length,
    zCols: z.length ? (z[0] ? z[0].length : 0) : 0,
    zSampleRow0: z[0] ? z[0].slice(0, 10) : undefined
  });

  const hover = z.map((rowZ, i) =>
    rowZ.map((val, j) => {
      const display = val == null ? "NA" : Number(val).toFixed(3);
      return `<b>${yOrder[i]}</b><br>${numericKeys[j]}: ${display}<extra></extra>`;
    })
  );

  return (
    <Card>
      <CardHeader title="Heatmap Differences" subheader={`Markers: ${numericKeys.length} — Groups: ${yOrder.length}`} />
      <CardContent>
        <Plot
          data={[
            {
              z,
              x: numericKeys,
              y: yOrder,
              type: "heatmap",
              colorscale: "RdBu",
              zmid: 0,
              hoverinfo: "text",
              text: hover,
              zauto: false,
            },
          ]}
          layout={{
            height: Math.max(360, yOrder.length * 28 + 120),
            margin: { l: Math.min(300, Math.max(120, yOrder.length * 12)), b: Math.min(400, numericKeys.length * 8) },
            yaxis: { automargin: true, tickfont: { size: 11 } },
            xaxis: { automargin: true, tickangle: -45, tickfont: { size: 10 } },
          }}
          config={{ responsive: true }}
          style={{ width: "100%" }}
        />
      </CardContent>
    </Card>
  );
};

export default StatHeatmap;