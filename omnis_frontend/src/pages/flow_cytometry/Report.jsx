import React, { useEffect, useState } from 'react';
import UMAPVisualization from "../../components/plot/UMAPVisualization";
import HeatmapVisualization from "../../components/plot/HeatmapVisualization";
import VolcanoPlot from "../../components/plot/VolcanoPlot";
import CohenEffect from "../../components/plot/CohenEffect";
import StatHeatmap from "../../components/plot/StatHeatmap";
import flowCytometryApi from '../../utils/ApiFlowCytometry';
import { useParams } from 'react-router-dom';



const ReportUmap = () => {
  const projectId = useParams().projectId;
  const pipelineId = useParams().pipelineId;
  const [umapData, setUmapData] = useState(null);
  const [volcanoData, setVolcanoData] = useState(null);
  const [cohenData, setCohenData] = useState(null);
  const [heatmapDiffData, setHeatmapDiffData] = useState(null);
  const [volcanoPath, setVolcanoPath] = useState(null);
  const [cohenPath, setCohenPath] = useState(null);
  const [heatmapPath, setHeatmapPath] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingTab, setLoadingTab] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    const fetchUmap = async () => {
      try {
        const res = await flowCytometryApi.get(`/api/v1/project/${projectId}/pipeline_results/${pipelineId}/umap`);
        setUmapData(res.data?.data ?? null);
      } catch (err) {
        setError(err.response?.data?.error || err.message || 'Error fetching UMAP');
      } finally {
        setLoading(false);
      }
    };
    fetchUmap();
  }, [projectId, pipelineId]);

  // map shortKey -> correct backend route (use the routes presenti in flow_cytometry_routes.py)
  const routeForKey = (shortKey) => {
    switch (shortKey) {
      case 'volcano':
        return `/api/v1/project/${projectId}/pipeline_results/${pipelineId}/volcano_plot`;
      case 'cohen':
        return `/api/v1/project/${projectId}/pipeline_results/${pipelineId}/cohen_kappa`;
      case 'heatmap_stats':
        return `/api/v1/project/${projectId}/pipeline_results/${pipelineId}/heatmap_differences`;
      default:
        return null;
    }
  };

  // restituisce { data: Array } | { path: string } | null
  const fetchResultEndpoint = async (shortKey) => {
    const route = routeForKey(shortKey);
    if (!route) return null;
    try {
      const res = await flowCytometryApi.get(route);
      console.log('Fetched raw', shortKey, res.data);

      // normalizza l'array dei record: priorità a res.data.data, poi res.data.rows, poi res.data (se è array)
      const raw = res.data;
      if (!raw) return null;

      if (Array.isArray(raw)) {
        return { data: raw };
      }
      if (Array.isArray(raw.data)) {
        return { data: raw.data };
      }
      if (Array.isArray(raw.rows)) {
        return { data: raw.rows };
      }
      // gestione caso annidato e altri wrapper possibili
      if (raw.data && typeof raw.data === 'object' && Array.isArray(raw.data.data)) {
        return { data: raw.data.data };
      }
      // se è un oggetto con campo "path"
      if (typeof raw.path === 'string') {
        return { path: raw.path };
      }

      // nulla riconosciuto
      console.log(`fetchResultEndpoint(${shortKey}): no array/path found`, raw);
      return null;
    } catch (err) {
      console.warn(`Error fetching ${shortKey}`, err);
      return null;
    }
  };

  const handleTabChange = async (index) => {
    setActiveTab(index);

    // Volcano
    if (index === 3 && volcanoData === null && volcanoPath === null) {
      setLoadingTab(true);
      const result = await fetchResultEndpoint('volcano');
      console.log("Report: fetched volcano result:", result);
      if (result) {
        if (result.path) setVolcanoPath(result.path);
        else if (Array.isArray(result.data)) setVolcanoData(result.data);
      }
      setLoadingTab(false);
    }

    // Cohen
    if (index === 4 && cohenData === null && cohenPath === null) {
      setLoadingTab(true);
      const result = await fetchResultEndpoint('cohen');
      console.log("Report: fetched cohen result:", result);
      if (result) {
        if (result.path) setCohenPath(result.path);
        else if (Array.isArray(result.data)) setCohenData(result.data);
      }
      setLoadingTab(false);
    }

    // Heatmap (assicuriamoci di passare l'array res.data.data esattamente come lo hai fornito)
    if (index === 5 && heatmapDiffData === null && heatmapPath === null) {
      setLoadingTab(true);
      const result = await fetchResultEndpoint('heatmap_stats');
      console.log("Report: fetched heatmap_stats result:", result);
      if (result) {
        if (result.path) {
          setHeatmapPath(result.path);
        } else if (Array.isArray(result.data)) {
          // PASSO proprio l'array contenuto in "data" così come richiesto
          setHeatmapDiffData(result.data);
          console.log("Report: heatmapDiffData set, rows:", result.data.length);
        }
      }
      setLoadingTab(false);
    }

    // Refetch UMAP se necessario
    if (index === 0 && umapData === null) {
      setLoadingTab(true);
      try {
        const res = await flowCytometryApi.get(`/api/v1/project/${projectId}/pipeline_results/${pipelineId}/umap`);
        setUmapData(res.data?.data ?? null);
      } catch (err) {
        setError(err.response?.data?.error || err.message || "Error fetching UMAP");
      } finally {
        setLoadingTab(false);
      }
    }
  };

  // helper to render backend file path as info / link (backend must expose a download route to actually fetch it)
  const renderPathInfo = (path) => {
    if (!path) return null;
    return (
      <div className="text-sm text-gray-600">
        File path on server: <code className="break-all">{path}</code>
        <div className="text-xs text-gray-500 mt-1">Per scaricarlo, assicurati che il backend esponga un endpoint di download.</div>
      </div>
    );
  };

  // Render page always — show messages inside each tab if data missing
  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">Flow Cytometry Analysis Report</h1>

      {error && <div className="text-center mb-4 text-red-600">Error: {error}</div>}

      <div className="bg-white shadow-md rounded-lg mb-6">
        <div className="flex border-b border-gray-200">
          <button className={`flex-1 py-3 text-center ${activeTab===0?'text-blue-600 border-b-4 border-blue-600':'text-gray-500'}`} onClick={()=>handleTabChange(0)}>UMAP</button>
          <button className={`flex-1 py-3 text-center ${activeTab===1?'text-blue-600 border-b-4 border-blue-600':'text-gray-500'}`} onClick={()=>handleTabChange(1)}>Heatmap</button>
          <button className={`flex-1 py-3 text-center ${activeTab===2?'text-blue-600 border-b-4 border-blue-600':'text-gray-500'}`} onClick={()=>handleTabChange(2)}>Both</button>
          <button className={`flex-1 py-3 text-center ${activeTab===3?'text-blue-600 border-b-4 border-blue-600':'text-gray-500'}`} onClick={()=>handleTabChange(3)}>Volcano</button>
          <button className={`flex-1 py-3 text-center ${activeTab===4?'text-blue-600 border-b-4 border-blue-600':'text-gray-500'}`} onClick={()=>handleTabChange(4)}>Cohen's d</button>
          <button className={`flex-1 py-3 text-center ${activeTab===5?'text-blue-600 border-b-4 border-blue-600':'text-gray-500'}`} onClick={()=>handleTabChange(5)}>Stats Heatmap</button>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg p-6">
        {activeTab === 0 && (
          loading ? <p className="text-center text-lg text-blue-600">Loading UMAP data...</p>
          : (umapData && Array.isArray(umapData) && umapData.length > 0 ? <UMAPVisualization data={umapData} /> : <p className="text-center text-gray-600">No UMAP plot available.</p>)
        )}

        {activeTab === 1 && (
          loading ? <p className="text-center text-lg text-blue-600">Loading data...</p>
          : (umapData && Array.isArray(umapData) && umapData.length > 0 ? <HeatmapVisualization data={umapData} /> : <p className="text-center text-gray-600">No heatmap available.</p>)
        )}

        {activeTab === 2 && (
          <div className="flex flex-col gap-6">
            {loading ? <p className="text-center text-lg text-blue-600">Loading...</p> :
              (umapData && Array.isArray(umapData) && umapData.length > 0 ? <><UMAPVisualization data={umapData} /><HeatmapVisualization data={umapData} /></> : <p className="text-center text-gray-600">No UMAP / heatmap available.</p>)
            }
          </div>
        )}

        {activeTab === 3 && (
          loadingTab ? <p className="text-center">Loading...</p> :
            (volcanoData ? <VolcanoPlot data={volcanoData} /> : (volcanoPath ? renderPathInfo(volcanoPath) : <p className="text-center text-gray-600">No volcano plot available.</p>))
        )}

        {activeTab === 4 && (
          loadingTab ? <p className="text-center">Loading...</p> :
            (cohenData ? <CohenEffect data={cohenData} /> : (cohenPath ? renderPathInfo(cohenPath) : <p className="text-center text-gray-600">No Cohen effect data available.</p>))
        )}

        {activeTab === 5 && (
          loadingTab ? <p className="text-center">Loading...</p> :
            (Array.isArray(heatmapDiffData) ? <StatHeatmap data={heatmapDiffData} /> : (heatmapPath ? renderPathInfo(heatmapPath) : <p className="text-center text-gray-600">No statistical heatmap available.</p>))
        )}
      </div>
    </div>
  );
};

const TabPanel = ({ children, value, index }) => {
  return value === index ? (
    <div role="tabpanel" id={`tabpanel-${index}`} aria-labelledby={`tab-${index}`} className="w-full">
      {children}
    </div>
  ) : null;
};

export default ReportUmap;