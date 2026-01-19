import React from "react";
import Plot from "react-plotly.js";
import { Card, CardHeader, CardContent, Typography } from "@mui/material";

const CohenEffect = ({ data, imageUrl, maxBars = 50 }) => {
  if (!data && !imageUrl) return <Typography>No Cohen effect data available.</Typography>;

  if (imageUrl) {
    return (
      <Card>
        <CardHeader title="Cohen's d / Effect Size" />
        <CardContent>
          <img src={imageUrl} alt="Cohen effect" style={{ maxWidth: "100%" }} />
        </CardContent>
      </Card>
    );
  }

  const rows = Array.isArray(data) ? data : [];
  if (rows.length === 0) return <Typography>No Cohen data available.</Typography>;

  // Expected keys in your dataset
  const markerKey = "marker";
  const effectKey = "cohen_d";
  const pKey = "p_value";
  const fdrKey = "fdr_corrected";
  const ciLowerKey = "ci_lower";
  const ciUpperKey = "ci_upper";
  const sigKey = "significant_fdr";
  const directionKey = "direction";

  // Filter valid rows and prepare numeric values
  const cleaned = rows
    .map((r) => {
      const effect = Number(r[effectKey]);
      const ciL = r[ciLowerKey] == null ? null : Number(r[ciLowerKey]);
      const ciU = r[ciUpperKey] == null ? null : Number(r[ciUpperKey]);
      return {
        raw: r,
        label: String(r[markerKey] ?? r.name ?? r.feature ?? ""),
        effect: Number.isFinite(effect) ? effect : null,
        p: r[pKey],
        fdr: r[fdrKey],
        ciL,
        ciU,
        sig: Boolean(r[sigKey]),
        dir: r[directionKey] ? String(r[directionKey]).toUpperCase() : null,
        absEffect: Number.isFinite(effect) ? Math.abs(effect) : 0,
      };
    })
    .filter((r) => r.effect !== null);

  if (cleaned.length === 0) return <Typography>No numeric Cohen data found.</Typography>;

  // sort by absolute effect (descending) and limit bars
  const selected = cleaned.sort((a, b) => b.absEffect - a.absEffect).slice(0, maxBars);

  const labels = selected.map((s) => s.label);
  const values = selected.map((s) => s.effect);

  // error bars: compute asymmetric if ci available
  const errorUpper = selected.map((s) => (s.ciU != null ? s.ciU - s.effect : 0));
  const errorLower = selected.map((s) => (s.ciL != null ? s.effect - s.ciL : 0));

  // color: use significance first, else direction
  const colors = selected.map((s) => {
    if (s.sig) return s.dir === "DOWN" ? "#d62728" : "#2ca02c"; // significant colored
    if (s.dir === "DOWN") return "#f28b82"; // light red
    if (s.dir === "UP") return "#90ee90"; // light green
    return "#888888"; // neutral
  });

  const hoverTexts = selected.map((s) => {
    const p = Number(s.p);
    const pStr = Number.isFinite(p) ? p.toExponential(2) : String(s.p ?? "");
    const fdrStr = s.fdr == null ? "" : String(s.fdr);
    return (
      `<b>${s.label}</b><br>` +
      `Cohen's d: ${s.effect.toFixed(3)}<br>` +
      `p-value: ${pStr}<br>` +
      (fdrStr ? `FDR: ${fdrStr}<br>` : "") +
      (s.ciL != null && s.ciU != null ? `CI: [${s.ciL.toFixed(3)}, ${s.ciU.toFixed(3)}]<br>` : "") +
      (s.raw.mean_difference != null ? `Mean diff: ${Number(s.raw.mean_difference).toFixed(3)}<br>` : "") +
      `Significant: ${s.sig ? "yes" : "no"}<extra></extra>`
    );
  });

  const layout = {
    height: Math.max(400, labels.length * 24 + 200),
    margin: { l: 160, r: 30, t: 40, b: Math.min(200, labels.length * 12 + 60) },
    yaxis: { title: "Cohen's d (effect size)" },
    xaxis: { automargin: true },
  };

  return (
    <Card>
      <CardHeader title="Cohen's d / Effect Size" subheader={`Top ${labels.length} features by |d|`} />
      <CardContent>
        <Plot
          data={[
            {
              x: labels,
              y: values,
              type: "bar",
              marker: { color: colors },
              error_y: {
                type: "data",
                array: errorUpper,
                arrayminus: errorLower,
                visible: true,
              },
              hoverinfo: "text",
              hovertemplate: hoverTexts,
            },
          ]}
          layout={{
            ...layout,
            xaxis: { ...layout.xaxis, tickangle: -45, tickfont: { size: 10 } },
          }}
          config={{ responsive: true }}
          style={{ width: "100%" }}
        />
      </CardContent>
    </Card>
  );
};

export default CohenEffect;