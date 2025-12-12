import React, { useEffect, useState, useRef } from 'react';
import { fetchPipelinesDataClustering } from '../../services/fcs_api';
import { Box, CircularProgress, Alert, Button } from '@mui/material';
import Typography from '@mui/material/Typography';
import * as d3 from 'd3';

const FCS_Clustering_Scatterplot = ({ projectId, pipelineId }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showPlot, setShowPlot] = useState(false);
    const svgRef = useRef();

    useEffect(() => {
        const getData = async () => {
            try {
                const clusteringData = await fetchPipelinesDataClustering(projectId, pipelineId);
                console.log('Clustering Data:', clusteringData);
                setData(clusteringData.data);
            } catch (err) {
                setError('Failed to load clustering data.');
            } finally {
                setLoading(false);
            }
        };
        getData();
    }, [projectId, pipelineId]);

    useEffect(() => {
        if (data && showPlot) {
            // Clear previous SVG content
            d3.select(svgRef.current).selectAll("*").remove();

            Object.keys(data).forEach((key) => {
                const svg = d3.select(svgRef.current)
                    .append('svg')
                    .attr('width', 1400)  // Increased width to accommodate legend
                    .attr('height', 800)
                    .style('margin', '10px');

                const margin = { top: 50, right: 600, bottom: 50, left: 100 }; // Increased right margin for legend
                const width = +svg.attr('width') - margin.left - margin.right;
                const height = +svg.attr('height') - margin.top - margin.bottom;

                const g = svg.append('g')
                    .attr('transform', `translate(${margin.left},${margin.top})`);

                const x = d3.scaleLinear()
                    .domain(d3.extent(data[key], d => d.UMAP_1)).nice()
                    .range([0, width]);

                const y = d3.scaleLinear()
                    .domain(d3.extent(data[key], d => d.UMAP_2)).nice()
                    .range([height, 0]);

                g.append('g')
                    .attr('class', 'axis axis--x')
                    .attr('transform', `translate(0,${height})`)
                    .call(d3.axisBottom(x));

                g.append('g')
                    .attr('class', 'axis axis--y')
                    .call(d3.axisLeft(y));

                // Calculate unique clusters and create a color scale
                const uniqueClusters = [...new Set(data[key].map(d => d.Leiden_Cluster))];
                const colorScale = d3.scaleOrdinal(d3.schemeCategory10.concat(d3.schemePaired, d3.schemeSet3));

                const dots = g.selectAll('.dot')
                    .data(data[key])
                    .enter().append('circle')
                    .attr('class', 'dot')
                    .attr('r', 1.5)
                    .attr('cx', d => x(d.UMAP_1))
                    .attr('cy', d => y(d.UMAP_2))
                    .style('fill', d => colorScale(d.Leiden_Cluster));

                // Define dimensions for the scrollable legend
                const legendWidth = 150;
                const legendHeight = 500;

                // Create a foreignObject con wrapper HTML
                const legendFO = svg.append('foreignObject')
                    .attr('x', width + margin.left + 20)
                    .attr('y', margin.top)
                    .attr('width', legendWidth)
                    // aggiungo 30px per la search bar + title
                    .attr('height', legendHeight + 30)
                    .append('xhtml:div')
                    .style('font-family', 'sans-serif');

                // 1) Search bar container
                const searchDiv = legendFO.append('div')
                    .style('margin-bottom', '6px');

                searchDiv.append('input')
                    .attr('type', 'text')
                    .attr('placeholder', 'Search cluster…')
                    .style('width', '100%')
                    .style('padding', '4px')
                    .style('box-sizing', 'border-box')
                    .on('input', function() {
                        const q = this.value.toLowerCase();
                        itemsContainer.selectAll('.legend-item')
                            .style('display', d => String(d).toLowerCase().includes(q) ? 'flex' : 'none');
                    });

                // ** NUOVO: Pulsante per ripristinare opacità **

                // modifico il colore del pulsante, per renderlo più visibile
                searchDiv.append('button')
                    .style('background-color', '#007bff')
                    .style('color', '#fff')
                    .style('border', 'none')
                    .style('border-radius', '8px')
                    .style('cursor', 'pointer')
                    .text('Ripristina Opacità')
                    .style('margin-top', '4px')
                    .style('padding', '4px 8px')
                    .style('font-size', '12px')
                    .on('click', () => {
                        // Riporta tutti i punti a opacità 1
                        dots.style('opacity', 1);
                    });

                // 2) Container scrollabile per i cluster
                const itemsContainer = legendFO.append('div')
                    .attr('class', 'legend-items')
                    .style('overflow-y', 'auto')
                    .style('height', legendHeight + 'px')
                    .style('width', legendWidth + 'px');

                // 3) Popolo i cluster ordinati
                uniqueClusters
                    .sort((a, b) => a - b)
                    .forEach(cluster => {
                        const item = itemsContainer.append('div')
                            .datum(cluster)
                            .attr('class', 'legend-item')
                            .style('display', 'flex')
                            .style('align-items', 'center')
                            .style('margin-bottom', '6px')
                            .style('cursor', 'pointer')
                            .on('click', () => {
                                dots.style('opacity', d => d.Leiden_Cluster === cluster ? 1 : 0.1);
                            });

                        item.append('div')
                            .style('width', '12px')
                            .style('height', '12px')
                            .style('background-color', colorScale(cluster))
                            .style('margin-right', '8px');

                        item.append('span')
                            .style('font-size', '12px')
                            .text(`Cluster ${cluster}`);
                    });
            });
        }
    }, [data, showPlot]);

    if (loading) return <Box display="flex" justifyContent="center" alignItems="center" height="100vh"><CircularProgress /></Box>;
    if (error) return <Alert severity="error">{error}</Alert>;

    return (
        <Box p={4}>
            <Button variant="contained" color="primary" onClick={() => setShowPlot(true)}>
                View Clustering Scatterplot
            </Button>
            <div ref={svgRef}></div>
        </Box>
    );
};

export default FCS_Clustering_Scatterplot;