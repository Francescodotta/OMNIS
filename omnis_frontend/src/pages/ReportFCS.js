import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import FCS_Clustering_Scatterplot from '../components/plot/FCS_Clustering_Scatterplot';
import FCS_Source_Scatterplot from '../components/plot/FCS_Source_Scatterplot';
import Heatmap from '../components/plot/FCS_Heatmap_Plot';
import Navbar from '../components/Navbar';

const ReportFCS = () => {
    const { projectId, pipelineId } = useParams();
    const [zoomHeatmap, setZoomHeatmap] = useState(false);

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <Navbar />
            
            {/* Header Section */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-500 text-white py-8 px-4 shadow-md">
                <div className="container mx-auto max-w-full">
                    <h1 className="text-3xl font-bold mb-2">FCS Analysis Report</h1>
                    <div className="flex items-center space-x-4 text-sm">
                        <div className="bg-white/20 rounded-full px-3 py-1">
                            Project ID: {projectId}
                        </div>
                        <div className="bg-white/20 rounded-full px-3 py-1">
                            Pipeline ID: {pipelineId}
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Content Container - Full width */}
            <div className="w-full px-6 py-8 flex-grow">
                {/* Summary Cards - Now horizontal at the top */}
                <div className="flex flex-wrap justify-center gap-6 mb-8">
                    <div className="bg-white rounded-lg shadow-md p-6 border-l-2 border-blue-600 min-w-[200px]">
                        <div className="text-gray-500 text-sm uppercase font-semibold mb-1">TOTAL CLUSTERS</div>
                        <div className="text-3xl font-bold text-gray-800">12</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-md p-6 border-l-2 border-teal-500 min-w-[200px]">
                        <div className="text-gray-500 text-sm uppercase font-semibold mb-1">SOURCE FILES</div>
                        <div className="text-3xl font-bold text-gray-800">8</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-md p-6 border-l-2 border-purple-500 min-w-[200px]">
                        <div className="text-gray-500 text-sm uppercase font-semibold mb-1">PARAMETERS</div>
                        <div className="text-3xl font-bold text-gray-800">24</div>
                    </div>
                </div>
                
                {/* Plots Section - Full width */}
                <div className="w-full space-y-8">
                    {/* Clustering Scatterplot */}
                    <div className="bg-white rounded-lg shadow-md overflow-hidden">
                        <div className="bg-blue-50 px-8 py-4 border-b border-blue-100 flex justify-between items-center">
                            <h2 className="text-xl font-semibold text-blue-800">
                                Clustering Scatterplot
                            </h2>
                            <div className="flex space-x-2">
                                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline mr-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                    Download
                                </button>
                                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline mr-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                                    </svg>
                                    Export
                                </button>
                            </div>
                        </div>
                        <div className="p-8">
                            <div className="text-sm text-gray-600 mb-4">
                                This plot shows the clustering results of your FCS data, with each point representing a cell and colors indicating different clusters.
                            </div>
                            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-[600px]">
                                <FCS_Clustering_Scatterplot projectId={projectId} pipelineId={pipelineId} />
                            </div>
                        </div>
                    </div>
                    
                    {/* Source File Scatterplot */}
                    <div className="bg-white rounded-lg shadow-md overflow-hidden">
                        <div className="bg-teal-50 px-8 py-4 border-b border-teal-100 flex justify-between items-center">
                            <h2 className="text-xl font-semibold text-teal-800">
                                Source File Scatterplot
                            </h2>
                            <div className="flex space-x-2">
                                <button className="text-teal-600 hover:text-teal-800 text-sm font-medium">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline mr-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                    Download
                                </button>
                                <button className="text-teal-600 hover:text-teal-800 text-sm font-medium">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline mr-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                                    </svg>
                                    Export
                                </button>
                            </div>
                        </div>
                        <div className="p-8">
                            <div className="text-sm text-gray-600 mb-4">
                                This plot visualizes the distribution of cells from different source files, helping you identify batch effects or sample-specific patterns.
                            </div>
                            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 min-h-[600px]">
                                <FCS_Source_Scatterplot projectId={projectId} pipelineId={pipelineId} />
                            </div>
                        </div>
                    </div>
                    
                    {/* Heatmap */}
                    <div className="bg-white rounded-lg shadow-md overflow-hidden relative">
                        <div className="bg-purple-50 px-8 py-4 border-b border-purple-100 flex justify-between items-center">
                            <h2 className="text-xl font-semibold text-purple-800">
                                Expression Heatmap
                            </h2>
                            <div className="flex space-x-2">
                                <button className="text-purple-600 hover:text-purple-800 text-sm font-medium">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline mr-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                    Download
                                </button>
                                <button className="text-purple-600 hover:text-purple-800 text-sm font-medium">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline mr-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                                    </svg>
                                    Export
                                </button>
                                <button
                                    onClick={() => setZoomHeatmap(true)}
                                    className="text-purple-600 hover:text-purple-800 text-sm font-medium"
                                >
                                    Zoom
                                </button>
                            </div>
                        </div>
                        <div className="p-8">
                            <div className="text-sm text-gray-600 mb-4">
                                The heatmap displays marker expression patterns across different clusters, helping you identify and characterize cell populations.
                            </div>
                            <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 w-full h-[800px] overflow-auto">
                                <Heatmap projectId={projectId} pipelineId={pipelineId} />
                            </div>
                        </div>
                    </div>

                    {/* Full-screen overlay */}
                    {zoomHeatmap && (
                        <div className="fixed inset-0 bg-white z-50 overflow-auto p-4">
                            <button
                                onClick={() => setZoomHeatmap(false)}
                                className="mb-4 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
                            >
                                Close
                            </button>
                            <div className="w-full h-full">
                                <Heatmap projectId={projectId} pipelineId={pipelineId} />
                            </div>
                        </div>
                    )}
                </div>
            </div>
            
            {/* Footer */}
            <footer className="bg-white border-t py-6">
                <div className="w-full px-6">
                    <div className="flex flex-col md:flex-row justify-between items-center">
                        <div className="flex items-center mb-4 md:mb-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-blue-600 mr-2">
                                <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                            </svg>
                            <span className="font-semibold text-gray-700">Omnis Platform</span>
                        </div>
                        <div className="text-gray-500 text-sm">
                            <span>Report generated: {new Date().toLocaleString()}</span>
                        </div>
                        <div className="flex space-x-4 mt-4 md:mt-0">
                            <a href="#" className="text-gray-500 hover:text-blue-600">
                                Help
                            </a>
                            <a href="#" className="text-gray-500 hover:text-blue-600">
                                Documentation
                            </a>
                            <a href="#" className="text-gray-500 hover:text-blue-600">
                                Support
                            </a>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default ReportFCS;