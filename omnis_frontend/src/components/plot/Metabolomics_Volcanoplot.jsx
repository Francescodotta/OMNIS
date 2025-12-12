import React, { useMemo } from "react";
import Plot from "react-plotly.js";

const MetabolomicsVolcanoPlot = ({ data, pValueThreshold = 0.05, log2fcThreshold = 1.0 }) => {
  // Processa i dati per il volcano plot
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return null;

    const metaboliteNames = data.map((item) => item.Metabolite);
    const log2fc = data.map((item) => item.Log2FC);
    const pValues = data.map((item) => item.P_Value);
    const negLog10Pval = data.map((item) => item.Neg_Log10_P);
    const meanGroup0 = data.map((item) => item.Mean_Group0);
    const meanGroup1 = data.map((item) => item.Mean_Group1);
    const tStats = data.map((item) => item.T_Statistic);
    const significant = data.map((item) => item.Significant);

    // Separa i punti significativi da quelli non significativi
    const upRegulated = { x: [], y: [], text: [], names: [] };
    const downRegulated = { x: [], y: [], text: [], names: [] };
    const notSignificant = { x: [], y: [], text: [], names: [] };

    data.forEach((item, i) => {
      const tooltip = `<b>${metaboliteNames[i]}</b><br>` +
        `Log2FC: ${log2fc[i]?.toFixed(4)}<br>` +
        `P-value: ${pValues[i]?.toExponential(2)}<br>` +
        `-Log10(P): ${negLog10Pval[i]?.toFixed(2)}<br>` +
        `Mean Group 0: ${meanGroup0[i]?.toExponential(2)}<br>` +
        `Mean Group 1: ${meanGroup1[i]?.toExponential(2)}<br>` +
        `T-Statistic: ${tStats[i]?.toFixed(3)}`;

      const isSignificant = pValues[i] < pValueThreshold && Math.abs(log2fc[i]) >= log2fcThreshold;

      if (isSignificant && log2fc[i] > 0) {
        upRegulated.x.push(log2fc[i]);
        upRegulated.y.push(negLog10Pval[i]);
        upRegulated.text.push(tooltip);
        upRegulated.names.push(metaboliteNames[i]);
      } else if (isSignificant && log2fc[i] < 0) {
        downRegulated.x.push(log2fc[i]);
        downRegulated.y.push(negLog10Pval[i]);
        downRegulated.text.push(tooltip);
        downRegulated.names.push(metaboliteNames[i]);
      } else {
        notSignificant.x.push(log2fc[i]);
        notSignificant.y.push(negLog10Pval[i]);
        notSignificant.text.push(tooltip);
        notSignificant.names.push(metaboliteNames[i]);
      }
    });

    return { upRegulated, downRegulated, notSignificant, log2fc, negLog10Pval };
  }, [data, pValueThreshold, log2fcThreshold]);

  if (!processedData) {
    return <div className="flex items-center justify-center h-full text-gray-500">No data available</div>;
  }

  const { upRegulated, downRegulated, notSignificant, log2fc, negLog10Pval } = processedData;

  // Calcola i limiti degli assi
  const xMin = Math.min(...log2fc) - 0.5;
  const xMax = Math.max(...log2fc) + 0.5;
  const yMax = Math.max(...negLog10Pval) + 0.5;

  return (
    <Plot
      data={[
        // Punti non significativi
        {
          x: notSignificant.x,
          y: notSignificant.y,
          text: notSignificant.text,
          mode: "markers",
          type: "scatter",
          name: "Not Significant",
          marker: {
            size: 8,
            color: "rgba(150, 150, 150, 0.5)",
            line: { width: 1, color: "rgba(100, 100, 100, 0.3)" },
          },
          hoverinfo: "text",
        },
        // Up-regulated (significativi positivi)
        {
          x: upRegulated.x,
          y: upRegulated.y,
          text: upRegulated.text,
          mode: "markers+text",
          type: "scatter",
          name: "Up-regulated",
          marker: {
            size: 12,
            color: "rgba(255, 99, 71, 0.8)",
            line: { width: 2, color: "darkred" },
            symbol: "diamond",
          },
          textposition: "top center",
          textfont: { size: 9, color: "darkred" },
          hoverinfo: "text",
        },
        // Down-regulated (significativi negativi)
        {
          x: downRegulated.x,
          y: downRegulated.y,
          text: downRegulated.text,
          mode: "markers+text",
          type: "scatter",
          name: "Down-regulated",
          marker: {
            size: 12,
            color: "rgba(30, 144, 255, 0.8)",
            line: { width: 2, color: "darkblue" },
            symbol: "diamond",
          },
          textposition: "top center",
          textfont: { size: 9, color: "darkblue" },
          hoverinfo: "text",
        },
        // Linea soglia p-value
        {
          x: [xMin, xMax],
          y: [-Math.log10(pValueThreshold), -Math.log10(pValueThreshold)],
          mode: "lines",
          name: `p-value = ${pValueThreshold}`,
          line: { color: "rgba(255, 165, 0, 0.7)", width: 2, dash: "dash" },
          hoverinfo: "skip",
        },
        // Linea soglia Log2FC positiva
        {
          x: [log2fcThreshold, log2fcThreshold],
          y: [0, yMax],
          mode: "lines",
          name: `Log2FC = ${log2fcThreshold}`,
          line: { color: "rgba(50, 205, 50, 0.7)", width: 2, dash: "dash" },
          hoverinfo: "skip",
        },
        // Linea soglia Log2FC negativa
        {
          x: [-log2fcThreshold, -log2fcThreshold],
          y: [0, yMax],
          mode: "lines",
          name: `Log2FC = -${log2fcThreshold}`,
          line: { color: "rgba(50, 205, 50, 0.7)", width: 2, dash: "dash" },
          showlegend: false,
          hoverinfo: "skip",
        },
      ]}
      layout={{
        title: {
          text: "🌋 Metabolomics Volcano Plot",
          font: { size: 24, color: "#2c3e50", family: "Arial Black" },
        },
        xaxis: {
          title: {
            text: "Log₂(Fold Change)",
            font: { size: 16, color: "#34495e" },
          },
          zeroline: true,
          zerolinecolor: "rgba(0,0,0,0.2)",
          zerolinewidth: 1,
          gridcolor: "rgba(0,0,0,0.05)",
          range: [xMin, xMax],
        },
        yaxis: {
          title: {
            text: "-Log₁₀(P-value)",
            font: { size: 16, color: "#34495e" },
          },
          zeroline: false,
          gridcolor: "rgba(0,0,0,0.05)",
          range: [0, yMax],
        },
        hovermode: "closest",
        legend: {
          orientation: "h",
          yanchor: "bottom",
          y: 1.02,
          xanchor: "center",
          x: 0.5,
          bgcolor: "rgba(255,255,255,0.8)",
          bordercolor: "rgba(0,0,0,0.1)",
          borderwidth: 1,
        },
        plot_bgcolor: "rgba(250, 250, 250, 1)",
        paper_bgcolor: "white",
        annotations: [
          {
            x: xMax - 0.3,
            y: yMax - 0.3,
            text: `<b>Up: ${upRegulated.x.length}</b>`,
            showarrow: false,
            font: { size: 14, color: "tomato" },
          },
          {
            x: xMin + 0.3,
            y: yMax - 0.3,
            text: `<b>Down: ${downRegulated.x.length}</b>`,
            showarrow: false,
            font: { size: 14, color: "dodgerblue" },
          },
        ],
        shapes: [
          // Sfondo quadrante up-regulated significativo
          {
            type: "rect",
            xref: "x",
            yref: "y",
            x0: log2fcThreshold,
            y0: -Math.log10(pValueThreshold),
            x1: xMax,
            y1: yMax,
            fillcolor: "rgba(255, 99, 71, 0.05)",
            line: { width: 0 },
            layer: "below",
          },
          // Sfondo quadrante down-regulated significativo
          {
            type: "rect",
            xref: "x",
            yref: "y",
            x0: xMin,
            y0: -Math.log10(pValueThreshold),
            x1: -log2fcThreshold,
            y1: yMax,
            fillcolor: "rgba(30, 144, 255, 0.05)",
            line: { width: 0 },
            layer: "below",
          },
        ],
      }}
      config={{
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToAdd: ["drawline", "drawopenpath", "eraseshape"],
        toImageButtonOptions: {
          format: "svg",
          filename: "volcano_plot",
          height: 800,
          width: 1200,
          scale: 2,
        },
      }}
      style={{ width: "100%", height: "100%" }}
    />
  );
};

export default MetabolomicsVolcanoPlot;