"""
Final report generator for OMNIS metabolomics pipeline.

Creates:
 - a report directory with copies of plots/datasets
 - a single PDF combining title, summary, plots (PCA, volcano, dendrogram, heatmap, kmeans)
 - CSV/JSON summaries included as text pages

Usage:
  run_final_report(results_dict, output_dir, run_id)
"""
import os
import time
import shutil
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# expected plot keys from statistical_analysis
STAT_PLOTS_ORDER = ['pca_plot', 'volcano_plot', 'dendrogram', 'heatmap', 'kmeans_plot']

def _safe_copy(src, dst_dir):
    if not src:
        return None
    try:
        if os.path.exists(src):
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, os.path.basename(src))
            shutil.copy2(src, dst)
            return dst
    except Exception:
        pass
    return None

def _add_image_page(pdf, img_path, title=None):
    plt.figure(figsize=(11, 8.5))
    plt.axis('off')
    if img_path and os.path.exists(img_path):
        try:
            img = plt.imread(img_path)
            plt.imshow(img)
            plt.title(title or "")
        except Exception:
            plt.text(0.5, 0.5, f"Could not render image: {os.path.basename(img_path)}", ha='center', va='center')
    else:
        plt.text(0.5, 0.5, f"Missing plot: {title or os.path.basename(img_path or '')}", ha='center', va='center')
    pdf.savefig()
    plt.close()

def _add_text_page(pdf, text, title=None):
    plt.figure(figsize=(11, 8.5))
    plt.axis('off')
    if title:
        plt.text(0.5, 0.95, title, ha='center', va='top', fontsize=16, fontweight='bold')
    plt.text(0.05, 0.9 if title else 0.95, text, ha='left', va='top', fontsize=10, family='monospace')
    pdf.savefig()
    plt.close()

def _add_dataframe_page(pdf, df, title=None, max_rows=20):
    txt = df.head(max_rows).to_string(index=False)
    if len(df) > max_rows:
        txt += f"\n\n... showing first {max_rows} of {len(df)} rows ..."
    _add_text_page(pdf, txt, title=title)

def generate_final_report(results_dict, output_path, run_id=None):
    out_dir = os.path.dirname(output_path)
    if not out_dir:
        out_dir = os.getcwd()
        output_path = os.path.join(out_dir, os.path.basename(output_path))
    os.makedirs(out_dir, exist_ok=True)

    assets_dir = os.path.join(out_dir, "report_assets")
    os.makedirs(assets_dir, exist_ok=True)

    # Collect plots and datasets to include
    qc = results_dict.get("qc_global", {})
    stat = results_dict.get("statistical_global", {})

    plots = {}
    # copy QC plots if any
    if isinstance(qc.get("plots"), dict):
        for k, v in qc["plots"].items():
            plots[f"qc_{k}"] = _safe_copy(v, assets_dir)

    # copy statistical plots (explicit order)
    stat_plots = stat.get("plots") if isinstance(stat.get("plots"), dict) else {}
    for key in STAT_PLOTS_ORDER:
        plots[key] = _safe_copy(stat_plots.get(key), assets_dir)

    # copy HMDB / statistical CSV if present
    hmdb_path = None
    # search hmdb path in results_dict (per-sample stored earlier)
    for v in results_dict.values():
        if isinstance(v, dict) and v.get("hmdb_search_results"):
            hmdb_path = v.get("hmdb_search_results")
            break
    if hmdb_path and os.path.exists(hmdb_path):
        plots['hmdb_csv'] = _safe_copy(hmdb_path, assets_dir)
    else:
        plots['hmdb_csv'] = None

    stat_csv = stat.get("csv_path") or results_dict.get("statistical_global", {}).get("csv_path")
    if stat_csv and os.path.exists(stat_csv):
        plots['stat_csv'] = _safe_copy(stat_csv, assets_dir)
    else:
        plots['stat_csv'] = None

    # Build PDF
    pdf_path = output_path
    with PdfPages(pdf_path) as pdf:
        # Title page
        _add_text_page(pdf,
                       text=f"Run ID: {run_id or results_dict.get('statistical_global',{}).get('run_id','N/A')}\nGenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
                       title="Metabolomics Pipeline - Final Report")

        # Executive summary
        summary_lines = []
        if 'qc_global' in results_dict:
            q = results_dict['qc_global']
            summary_lines.append("Quality Control:")
            summary_lines.append(f"  report: {os.path.basename(q.get('report_path','N/A'))}")
            summary_lines.append(f"  csv: {os.path.basename(q.get('csv_path','N/A'))}")
        if 'statistical_global' in results_dict:
            s = results_dict['statistical_global']
            summary_lines.append("Statistical Analysis:")
            summary_lines.append(f"  json: {os.path.basename(s.get('json_path','N/A'))}")
            summary_lines.append(f"  csv: {os.path.basename(s.get('csv_path','N/A'))}")
        _add_text_page(pdf, "\n".join(summary_lines), title="Executive Summary")

        # Include QC plots (all found)
        if qc.get("plots"):
            for k, p in qc.get("plots", {}).items():
                img = plots.get(f"qc_{k}", None) or p
                _add_image_page(pdf, img, title=f"QC - {k}")

        # Include statistical plots in fixed order with placeholders
        for key in STAT_PLOTS_ORDER:
            title = key.replace('_', ' ').upper()
            img = plots.get(key)
            _add_image_page(pdf, img, title=f"Statistics - {title}")

        # Include HMDB table (if available)
        if plots.get('hmdb_csv'):
            try:
                df_h = pd.read_csv(plots['hmdb_csv'])
                _add_dataframe_page(pdf, df_h, title="HMDB Search Results (sample)")
            except Exception:
                _add_text_page(pdf, "HMDB CSV present but could not be read", title="HMDB Search Results")

        # Include statistical tests CSV (if available)
        if plots.get('stat_csv'):
            try:
                df_s = pd.read_csv(plots['stat_csv'])
                _add_dataframe_page(pdf, df_s, title="Univariate Statistical Tests (top rows)")
            except Exception:
                _add_text_page(pdf, "Statistical CSV present but could not be read", title="Statistical Tests")

        # Footer page
        _add_text_page(pdf, "End of report\n", title="Footer")

    return pdf_path

def run_final_report(results_dict, output_dir=None, run_id=None):
    if output_dir is None:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    if run_id is None:
        run_id = f"final_report_{int(time.time())}"
    pdf_name = f"{run_id}.pdf"
    pdf_path = os.path.join(output_dir, pdf_name)

    generated_pdf = generate_final_report(results_dict, pdf_path, run_id)

    print(f"Final report generated: {generated_pdf}")
    return generated_pdf