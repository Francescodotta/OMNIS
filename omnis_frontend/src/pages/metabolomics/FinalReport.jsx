import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
    fetchVolcanoPlotData, 
    fetchPipelineDetails,
    fetchMetabolomicsPipelineResults 
} from "../../services/metabolomics_api";
import MetabolomicsVolcanoPlot from "../../components/plot/Metabolomics_Volcanoplot";

// Icons
import { 
    BeakerIcon, 
    ArrowLeftIcon, 
    ChartBarIcon,
    DocumentArrowDownIcon,
    AdjustmentsHorizontalIcon,
    ExclamationTriangleIcon,
    CheckCircleIcon,
    ClockIcon
} from "@heroicons/react/24/outline";

const FinalReport = () => {
    const { projectId, pipelineId } = useParams();
    const navigate = useNavigate();

    // State management
    const [volcanoData, setVolcanoData] = useState([]);
    const [pipelineDetails, setPipelineDetails] = useState(null);
    const [pipelineResults, setPipelineResults] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Threshold controls
    const [pValueThreshold, setPValueThreshold] = useState(0.05);
    const [log2fcThreshold, setLog2fcThreshold] = useState(1.0);
    const [showControls, setShowControls] = useState(false);

    // Fetch all data
    const fetchAllData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            // Fetch volcano plot data
            const volcanoResponse = await fetchVolcanoPlotData(projectId, pipelineId);
            setVolcanoData(volcanoResponse);

            // Fetch pipeline details
            try {
                const detailsResponse = await fetchPipelineDetails(projectId, pipelineId);
                setPipelineDetails(detailsResponse);
            } catch (e) {
                console.warn("Could not fetch pipeline details:", e);
            }

            // Fetch pipeline results
            try {
                const resultsResponse = await fetchMetabolomicsPipelineResults(projectId, pipelineId);
                setPipelineResults(resultsResponse);
            } catch (e) {
                console.warn("Could not fetch pipeline results:", e);
            }

        } catch (err) {
            console.error("Error fetching data:", err);
            setError(err.message || "Failed to load report data");
        } finally {
            setLoading(false);
        }
    }, [projectId, pipelineId]);

    useEffect(() => {
        fetchAllData();
    }, [fetchAllData]);

    // Calculate statistics from volcano data
    const calculateStats = useCallback(() => {
        if (!volcanoData || volcanoData.length === 0) {
            return { total: 0, significant: 0, upRegulated: 0, downRegulated: 0 };
        }

        const significant = volcanoData.filter(
            item => item.P_Value < pValueThreshold && Math.abs(item.Log2FC) >= log2fcThreshold
        );

        const upRegulated = significant.filter(item => item.Log2FC > 0);
        const downRegulated = significant.filter(item => item.Log2FC < 0);

        return {
            total: volcanoData.length,
            significant: significant.length,
            upRegulated: upRegulated.length,
            downRegulated: downRegulated.length
        };
    }, [volcanoData, pValueThreshold, log2fcThreshold]);

    const stats = calculateStats();

    // Export data as CSV
    const handleExportCSV = () => {
        if (!volcanoData || volcanoData.length === 0) return;

        const headers = Object.keys(volcanoData[0]).join(",");
        const rows = volcanoData.map(item => Object.values(item).join(",")).join("\n");
        const csv = `${headers}\n${rows}`;

        const blob = new Blob([csv], { type: "text/csv" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `volcano_plot_data_${pipelineId}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // Loading state
    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-500 mx-auto mb-4"></div>
                    <p className="text-white text-xl font-semibold">Loading Report...</p>
                    <p className="text-gray-400 mt-2">🦍 Apes are analyzing your data...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-red-900 to-slate-900 flex items-center justify-center">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 max-w-md text-center">
                    <ExclamationTriangleIcon className="h-16 w-16 text-red-400 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-white mb-2">Error Loading Report</h2>
                    <p className="text-gray-300 mb-6">{error}</p>
                    <button
                        onClick={() => navigate(-1)}
                        className="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-all"
                    >
                        Go Back
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            {/* Header */}
            <header className="bg-black/30 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => navigate(-1)}
                                className="p-2 hover:bg-white/10 rounded-lg transition-all"
                            >
                                <ArrowLeftIcon className="h-6 w-6 text-white" />
                            </button>
                            <div className="flex items-center space-x-3">
                                <BeakerIcon className="h-8 w-8 text-purple-400" />
                                <div>
                                    <h1 className="text-xl font-bold text-white">
                                        Metabolomics Final Report
                                    </h1>
                                    <p className="text-sm text-gray-400">
                                        Pipeline: {pipelineId} | Project: {projectId}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center space-x-3">
                            <button
                                onClick={() => setShowControls(!showControls)}
                                className={`p-2 rounded-lg transition-all ${
                                    showControls 
                                        ? "bg-purple-500 text-white" 
                                        : "bg-white/10 text-gray-300 hover:bg-white/20"
                                }`}
                            >
                                <AdjustmentsHorizontalIcon className="h-6 w-6" />
                            </button>
                            <button
                                onClick={handleExportCSV}
                                className="flex items-center space-x-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all"
                            >
                                <DocumentArrowDownIcon className="h-5 w-5" />
                                <span>Export CSV</span>
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Controls Panel */}
            {showControls && (
                <div className="bg-black/20 backdrop-blur-lg border-b border-white/10">
                    <div className="max-w-7xl mx-auto px-4 py-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    P-Value Threshold: {pValueThreshold}
                                </label>
                                <input
                                    type="range"
                                    min="0.001"
                                    max="0.1"
                                    step="0.001"
                                    value={pValueThreshold}
                                    onChange={(e) => setPValueThreshold(parseFloat(e.target.value))}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>0.001</span>
                                    <span>0.05</span>
                                    <span>0.1</span>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Log2FC Threshold: ±{log2fcThreshold}
                                </label>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="3"
                                    step="0.1"
                                    value={log2fcThreshold}
                                    onChange={(e) => setLog2fcThreshold(parseFloat(e.target.value))}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>0.5</span>
                                    <span>1.5</span>
                                    <span>3.0</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-8">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <StatCard
                        title="Total Metabolites"
                        value={stats.total}
                        icon={<BeakerIcon className="h-6 w-6" />}
                        color="blue"
                    />
                    <StatCard
                        title="Significant"
                        value={stats.significant}
                        icon={<CheckCircleIcon className="h-6 w-6" />}
                        color="green"
                    />
                    <StatCard
                        title="Up-Regulated"
                        value={stats.upRegulated}
                        icon={<ChartBarIcon className="h-6 w-6" />}
                        color="red"
                    />
                    <StatCard
                        title="Down-Regulated"
                        value={stats.downRegulated}
                        icon={<ChartBarIcon className="h-6 w-6 rotate-180" />}
                        color="cyan"
                    />
                </div>

                {/* Pipeline Info */}
                {pipelineDetails && (
                    <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 mb-8 border border-white/10">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                            <ClockIcon className="h-5 w-5 mr-2 text-purple-400" />
                            Pipeline Information
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <InfoItem label="Status" value={pipelineDetails.status || "Completed"} />
                            <InfoItem label="Created" value={pipelineDetails.created_at || "N/A"} />
                            <InfoItem label="Pipeline ID" value={pipelineId} />
                            <InfoItem label="Project ID" value={projectId} />
                        </div>
                    </div>
                )}

                {/* Volcano Plot */}
                <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
                    <div className="p-6 bg-gradient-to-r from-purple-600 to-pink-600">
                        <h2 className="text-2xl font-bold text-white flex items-center">
                            🌋 Volcano Plot Analysis
                        </h2>
                        <p className="text-purple-100 mt-1">
                            Differential expression analysis of {stats.total} metabolites
                        </p>
                    </div>
                    <div className="p-4" style={{ height: "600px" }}>
                        {volcanoData && volcanoData.length > 0 ? (
                            <MetabolomicsVolcanoPlot
                                data={volcanoData}
                                pValueThreshold={pValueThreshold}
                                log2fcThreshold={log2fcThreshold}
                            />
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-500">
                                <div className="text-center">
                                    <BeakerIcon className="h-16 w-16 mx-auto mb-4 text-gray-400" />
                                    <p className="text-xl">No data available for volcano plot</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Significant Metabolites Table */}
                {volcanoData && volcanoData.length > 0 && (
                    <div className="mt-8 bg-white/5 backdrop-blur-lg rounded-2xl overflow-hidden border border-white/10">
                        <div className="p-6 border-b border-white/10">
                            <h3 className="text-xl font-bold text-white">
                                📊 Significant Metabolites
                            </h3>
                            <p className="text-gray-400 mt-1">
                                Metabolites with p-value {"<"} {pValueThreshold} and |Log2FC| ≥ {log2fcThreshold}
                            </p>
                        </div>
                        <div className="overflow-x-auto max-h-96">
                            <table className="w-full">
                                <thead className="bg-white/5 sticky top-0">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">
                                            Metabolite
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">
                                            Log2FC
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">
                                            P-Value
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">
                                            -Log10(P)
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">
                                            Regulation
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {volcanoData
                                        .filter(item => 
                                            item.P_Value < pValueThreshold && 
                                            Math.abs(item.Log2FC) >= log2fcThreshold
                                        )
                                        .sort((a, b) => a.P_Value - b.P_Value)
                                        .map((item, index) => (
                                            <tr key={index} className="hover:bg-white/5 transition-colors">
                                                <td className="px-6 py-4 text-sm text-white font-medium">
                                                    {item.Metabolite}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-300">
                                                    {item.Log2FC?.toFixed(4)}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-300">
                                                    {item.P_Value?.toExponential(2)}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-300">
                                                    {item.Neg_Log10_P?.toFixed(2)}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                                        item.Log2FC > 0 
                                                            ? "bg-red-500/20 text-red-400" 
                                                            : "bg-blue-500/20 text-blue-400"
                                                    }`}>
                                                        {item.Log2FC > 0 ? "↑ Up" : "↓ Down"}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                </tbody>
                            </table>
                            {stats.significant === 0 && (
                                <div className="p-8 text-center text-gray-400">
                                    No significant metabolites found with current thresholds
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

// Stat Card Component
const StatCard = ({ title, value, icon, color }) => {
    const colorClasses = {
        blue: "from-blue-500 to-blue-600",
        green: "from-green-500 to-green-600",
        red: "from-red-500 to-red-600",
        cyan: "from-cyan-500 to-cyan-600",
        purple: "from-purple-500 to-purple-600",
    };

    return (
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10 hover:border-white/20 transition-all">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-gray-400 text-sm">{title}</p>
                    <p className="text-3xl font-bold text-white mt-1">{value}</p>
                </div>
                <div className={`p-3 rounded-lg bg-gradient-to-br ${colorClasses[color]} text-white`}>
                    {icon}
                </div>
            </div>
        </div>
    );
};

// Info Item Component
const InfoItem = ({ label, value }) => (
    <div>
        <p className="text-gray-500 text-xs uppercase">{label}</p>
        <p className="text-white font-medium">{value}</p>
    </div>
);

export default FinalReport;