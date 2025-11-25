import React from "react";
import { useParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import MetabolomicsResultTable from '../components/dashboards/metabolomics/PipelineResults';

const ReportMetabolomicsPipeline = () => {
    const { projectId, pipelineId } = useParams();

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <Navbar />
            {/* HEADER SECTION */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-500 text-white py-8 px-4 shadow-md">
                <div className="container mx-auto">
                    <h1 className="text-3xl font-bold mb-2">Metabolomics Pipeline Report</h1>
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

            {/* CONTENT SECTION */}
            <div className="flex-1 container mx-auto px-2 py-6 flex flex-col items-center">
                <div className="w-full bg-white rounded-xl shadow-lg p-6" style={{ minWidth: 0 }}>
                    <MetabolomicsResultTable projectId={projectId} pipelineId={pipelineId} />
                </div>
            </div>
        </div>
    );
};

export default ReportMetabolomicsPipeline;

