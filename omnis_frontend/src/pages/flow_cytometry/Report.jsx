import React, { useEffect, useState } from 'react';
import UMAPVisualization from "../../components/plot/UMAPVisualization";
import HeatmapVisualization from "../../components/plot/HeatmapVisualization";
import flowCytometryApi from '../../utils/ApiFlowCytometry';
import { useParams } from 'react-router-dom';

const TabPanel = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      className="w-full"
    >
      {value === index && <div className="pt-4">{children}</div>}
    </div>
  );
};

const ReportUmap = () => {
  const projectId = useParams().projectId;
  const pipelineId = useParams().pipelineId;
  const [umapData, setUmapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    const fetchUmapData = async () => {
      try {
        const response = await flowCytometryApi.get(
          `/api/v1/project/${projectId}/pipeline_results/${pipelineId}/umap`
        );
        setUmapData(response.data.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUmapData();
  }, [projectId, pipelineId]);

  const handleTabChange = (index) => {
    setActiveTab(index);
  };

  if (loading) {
    return <p className="text-center text-lg text-blue-600">Loading UMAP data...</p>;
  }
  if (error) {
    return <p className="text-center text-lg text-red-600">Error: {error}</p>;
  }
  if (!umapData || umapData.length === 0) {
    return <p className="text-center text-lg text-gray-600">No UMAP data available.</p>;
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">
        Flow Cytometry Analysis Report
      </h1>

      {/* Tabs */}
      <div className="bg-white shadow-md rounded-lg mb-6">
        <div className="flex border-b border-gray-200">
          <button
            className={`flex-1 py-3 text-center text-lg font-medium ${
              activeTab === 0 ? 'text-blue-600 border-b-4 border-blue-600' : 'text-gray-500'
            }`}
            onClick={() => handleTabChange(0)}
          >
            UMAP Visualization
          </button>
          <button
            className={`flex-1 py-3 text-center text-lg font-medium ${
              activeTab === 1 ? 'text-blue-600 border-b-4 border-blue-600' : 'text-gray-500'
            }`}
            onClick={() => handleTabChange(1)}
          >
            Heatmap
          </button>
          <button
            className={`flex-1 py-3 text-center text-lg font-medium ${
              activeTab === 2 ? 'text-blue-600 border-b-4 border-blue-600' : 'text-gray-500'
            }`}
            onClick={() => handleTabChange(2)}
          >
            Both
          </button>
        </div>
      </div>

      {/* Tab Panels */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <TabPanel value={activeTab} index={0}>
          <UMAPVisualization data={umapData} />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <HeatmapVisualization data={umapData} />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <div className="flex flex-col gap-6">
            <UMAPVisualization data={umapData} />
            <HeatmapVisualization data={umapData} />
          </div>
        </TabPanel>
      </div>
    </div>
  );
};

export default ReportUmap;