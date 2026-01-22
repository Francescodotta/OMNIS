import React from "react";
import Plot from "react-plotly.js";
import { Card, CardHeader, CardContent, Typography } from "@mui/material";
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

const VolcanoPlot = ({ data, imageUrl }) => {
  if (!data && !imageUrl) return <Typography>No volcano data available.</Typography>;

  // If image is provided, show it
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

  // 🎯 Identifica le colonne chiave con priorità ai nomi standardizzati
  const firstRow = rows[0];
  
  // Trova la colonna X (log2FoldChange, mean_difference, logFC)
  const xKey = firstRow.log2FoldChange !== undefined ? 'log2FoldChange'
    : firstRow.mean_difference !== undefined ? 'mean_difference'
    : firstRow.logFC !== undefined ? 'logFC'
    : Object.keys(firstRow).find(k => /log2?fold|logfc|mean_diff/i.test(k));

  // Trova la colonna Y (p_value, pvalue, fdr_corrected)
  const pKey = firstRow.p_value !== undefined ? 'p_value'
    : firstRow.pvalue !== undefined ? 'pvalue'
    : firstRow.fdr_corrected !== undefined ? 'fdr_corrected'
    : Object.keys(firstRow).find(k => /p(.?_)?value|pval|fdr|p$/i.test(k));

  // Trova la colonna per le label (gene, marker, name)
  const labelKey = firstRow.gene !== undefined ? 'gene'
    : firstRow.marker !== undefined ? 'marker'
    : firstRow.name !== undefined ? 'name'
    : Object.keys(firstRow).find(k => /gene|marker|name/i.test(k));

  if (!xKey || !pKey) {
    return <Typography>Volcano data format not recognized. Missing log2FC or p-value columns.</Typography>;
  }

  console.log(`Using columns - X: ${xKey}, Y: ${pKey}, Label: ${labelKey}`);

  // 📊 Prepara i dati per il plot
  const x = rows.map(r => Number(r[xKey]) || 0);
  const y = rows.map(r => {
    const p = Number(r[pKey]);
    return Number.isFinite(p) && p > 0 ? -Math.log10(p) : 0;
  });
  const labels = rows.map(r => r[labelKey] || r.gene || r.marker || "Unknown");

  // 🎨 Colora i punti in base a significatività e fold change
  const colors = rows.map((r, i) => {
    const fc = Number(r[xKey]) || 0;
    // 🔧 FIX: Usa pKey invece di hardcodare 'p_value'
    const pValue = Number(r[pKey]) || 1;
    const fdr = Number(r.fdr_corrected);
    const hasFDR = r.fdr_corrected !== undefined && !isNaN(fdr);
    
    console.log(`Row ${i} (${labels[i]}): FC=${fc.toFixed(3)}, p=${pValue.toFixed(6)}, FDR=${hasFDR ? fdr.toFixed(6) : 'N/A'}`);
    
    // Caso 1: FDR disponibile e significativo con alto FC
    if (hasFDR && fdr < 0.05 && Math.abs(fc) > 1) {
      return fc > 0 ? 'red' : 'blue'; // Rosso per upregulated, blu per downregulated
    } 
    // Caso 2: FDR disponibile e significativo ma FC basso
    else if (hasFDR && fdr < 0.05) {
      return 'orange'; // Significativo (FDR) ma fold change basso
    }
    // Caso 3: ⚠️ P-value significativo ma SENZA correzione FDR
    else if (!hasFDR && pValue < 0.05 && Math.abs(fc) > 1) {
      console.log(`⚠️ Uncorrected significant: ${labels[i]} (p=${pValue})`);
      return '#FF00FF'; // Magenta - Attenzione: significativo senza FDR!
    }
    // Caso 4: Solo p-value significativo (anche senza alto FC)
    else if (!hasFDR && pValue < 0.05) {
      return '#9C27B0'; // Viola - p significativo ma FC basso
    }
    // Caso 5: FC alto ma non significativo
    else if (Math.abs(fc) > 1) {
      return 'green'; // Fold change alto ma non significativo
    }
    // Caso 6: Non significativo
    return 'gray';
  });

  // 📏 Calcola dimensioni dei punti in base a Cohen's d (se disponibile)
  const sizes = rows.map(r => {
    const cohen = Math.abs(Number(r.cohen_d) || 0);
    return Math.min(12, 6 + cohen * 3); // Size tra 6 e 12
  });

  // 🏷️ Tooltip migliorato con tutte le info disponibili
  const hovertext = rows.map((r, i) => {
    const hasFDR = r.fdr_corrected !== undefined && !isNaN(Number(r.fdr_corrected));
    const parts = [
      `<b>${labels[i]}</b>`,
      `log2FC: ${x[i].toFixed(3)}`,
      `-log10(p): ${y[i].toFixed(3)}`,
      `p-value: ${Number(r[pKey]).toExponential(2)}`
    ];
    
    if (hasFDR) {
      parts.push(`FDR: ${Number(r.fdr_corrected).toExponential(2)}`);
    } else {
      parts.push(`⚠️ FDR: Not corrected`);
    }
    
    if (r.cohen_d !== undefined) {
      parts.push(`Cohen's d: ${Number(r.cohen_d).toFixed(3)}`);
    }
    if (r.ci_lower !== undefined && r.ci_upper !== undefined) {
      parts.push(`95% CI: [${Number(r.ci_lower).toFixed(2)}, ${Number(r.ci_upper).toFixed(2)}]`);
    }
    
    return parts.join('<br>');
  });

  // Conta i marker in ogni categoria per la legenda
  const stats = {
    upregulated: colors.filter(c => c === 'red').length,
    downregulated: colors.filter(c => c === 'blue').length,
    significant: colors.filter(c => c === 'orange').length,
    uncorrectedHighFC: colors.filter(c => c === '#FF00FF').length,
    uncorrectedLowFC: colors.filter(c => c === '#9C27B0').length,
    highFC: colors.filter(c => c === 'green').length,
    notSignificant: colors.filter(c => c === 'gray').length
  };

  return (
    <Card>
      <CardHeader 
        title="Volcano Plot" 
        subheader={`${rows.length} markers | Red/Blue: FDR<0.05 & |log2FC|>1`}
      />
      <CardContent>
        <Plot
          data={[{
            x,
            y,
            text: labels,
            mode: "markers",
            marker: {
              size: sizes,
              color: colors,
              opacity: 0.7,
              line: { width: 0.5, color: 'white' }
            },
            hovertext: hovertext,
            hoverinfo: 'text',
            type: 'scatter'
          }]}
          layout={{
            height: 600,
            xaxis: {
              title: "log2 Fold Change (Mean Difference)",
              zeroline: true,
              zerolinewidth: 2,
              zerolinecolor: 'black'
            },
            yaxis: {
              title: "-log10(p-value)",
              zeroline: false
            },
            hovermode: "closest",
            shapes: [
              // Linea verticale per fold change threshold
              { type: 'line', x0: -1, x1: -1, y0: 0, y1: Math.max(...y), 
                line: { color: 'gray', width: 1, dash: 'dash' } },
              { type: 'line', x0: 1, x1: 1, y0: 0, y1: Math.max(...y),
                line: { color: 'gray', width: 1, dash: 'dash' } },
              // Linea orizzontale per p-value threshold (0.05)
              { type: 'line', x0: Math.min(...x), x1: Math.max(...x), y0: -Math.log10(0.05), y1: -Math.log10(0.05),
                line: { color: 'red', width: 1, dash: 'dash' } }
            ],
            annotations: [
              { x: 1, y: Math.max(...y) * 0.95, text: 'FC threshold', showarrow: false, font: { size: 10, color: 'gray' } },
              { x: Math.min(...x) * 0.95, y: -Math.log10(0.05), text: 'p=0.05', showarrow: false, font: { size: 10, color: 'red' } }
            ]
          }}
          config={{ responsive: true, displayModeBar: true }}
          style={{ width: "100%" }}
        />
        
        {/* Legenda personalizzata con conteggi */}
        <div style={{ marginTop: '15px', fontSize: '12px' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '10px' }}>
            <span style={{ color: 'red', fontWeight: 'bold' }}>
              ● Upregulated ({stats.upregulated}) - FDR&lt;0.05, log2FC&gt;1
            </span>
            <span style={{ color: 'blue', fontWeight: 'bold' }}>
              ● Downregulated ({stats.downregulated}) - FDR&lt;0.05, log2FC&lt;-1
            </span>
            <span style={{ color: 'orange' }}>
              ● Significant ({stats.significant}) - FDR&lt;0.05 only
            </span>
            <span style={{ color: '#FF00FF', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <WarningAmberIcon sx={{ fontSize: 14 }} />
              <span>⚠️ Uncorrected High FC ({stats.uncorrectedHighFC}) - p&lt;0.05, NO FDR, |log2FC|&gt;1</span>
            </span>
            <span style={{ color: '#9C27B0', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <WarningAmberIcon sx={{ fontSize: 14 }} />
              <span>⚠️ Uncorrected Low FC ({stats.uncorrectedLowFC}) - p&lt;0.05, NO FDR</span>
            </span>
            <span style={{ color: 'green' }}>
              ● High FC ({stats.highFC}) - |log2FC|&gt;1 only
            </span>
            <span style={{ color: 'gray' }}>
              ● Not significant ({stats.notSignificant})
            </span>
          </div>
          
          {/* Alert box se ci sono marker non corretti */}
          {(stats.uncorrectedHighFC + stats.uncorrectedLowFC) > 0 && (
            <div style={{ 
              marginTop: '15px', 
              padding: '10px', 
              backgroundColor: '#FFF3E0', 
              border: '1px solid #FF9800',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <WarningAmberIcon sx={{ color: '#FF9800' }} />
              <span style={{ color: '#E65100' }}>
                <strong>Warning:</strong> {stats.uncorrectedHighFC + stats.uncorrectedLowFC} marker(s) show significance without FDR correction. 
                Consider multiple testing correction before drawing conclusions.
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default VolcanoPlot;