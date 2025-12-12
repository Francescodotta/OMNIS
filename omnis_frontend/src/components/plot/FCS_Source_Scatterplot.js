import React, { useEffect, useState, useRef } from 'react';
import { fetchPipelinesDataClustering } from '../../services/fcs_api';
import { Box, CircularProgress, Alert, Button } from '@mui/material';
import Typography from '@mui/material/Typography';
import * as d3 from 'd3';

const FCS_Source_Scatterplot = ({ projectId, pipelineId }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showPlot, setShowPlot] = useState(false);
    const svgRef = useRef();

    useEffect(() => {
        const getData = async () => {
            try {
                const clusteringData = await fetchPipelinesDataClustering(projectId, pipelineId);
                console.log('Source Data:', clusteringData);
                setData(clusteringData.data);
            } catch (err) {
                setError('Failed to load source data.');
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
                    .attr('width', 1400)
                    .attr('height', 800)
                    .style('margin', '10px');

                const margin = { top: 50, right: 600, bottom: 50, left: 100 }; // Increased right margin for potentially longer source file names
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

                // Calculate unique source files and create a color scale
                const uniqueSources = [...new Set(data[key].map(d => d['source_file']))];
                const colorScale = d3.scaleOrdinal(d3.schemeCategory10.concat(d3.schemePaired, d3.schemeSet3));

                const dots = g.selectAll('.dot')
                    .data(data[key])
                    .enter().append('circle')
                    .attr('class', 'dot')
                    .attr('r', 1.5)
                    .attr('cx', d => x(d.UMAP_1))
                    .attr('cy', d => y(d.UMAP_2))
                    .style('fill', d => colorScale(d['source_file']));

                // Add legend
                const legend = svg.append('g')
                    .attr('transform', `translate(${width + margin.left + 20},${margin.top})`);

                uniqueSources.forEach((source, i) => {
                    legend.append('rect')
                        .attr('x', 0)
                        .attr('y', i * 20)
                        .attr('width', 10)
                        .attr('height', 10)
                        .style('fill', colorScale(source))
                        .style('cursor', 'pointer')
                        .on('click', () => {
                            // Highlight points belonging to the clicked source
                            dots.style('opacity', d => d['source_file'] === source ? 1 : 0.1);
                        });

                    legend.append('text')
                        .attr('x', 20)
                        .attr('y', i * 20 + 10)
                        .attr('text-anchor', 'start')
                        .style('font-size', '12px')
                        .style('cursor', 'pointer')
                        .text(source)
                        .on('click', () => {
                            // Highlight points belonging to the clicked source
                            dots.style('opacity', d => d['source_file'] === source ? 1 : 0.1);
                        });
                });
            });
        }
    }, [data, showPlot]);

    if (loading) return <Box display="flex" justifyContent="center" alignItems="center" height="100vh"><CircularProgress /></Box>;
    if (error) return <Alert severity="error">{error}</Alert>;

    return (
        <Box p={4}>
            <Button variant="contained" color="primary" onClick={() => setShowPlot(true)}>
                View Source File Scatterplot
            </Button>
            <div ref={svgRef}></div>
        </Box>
    );
};

export default FCS_Source_Scatterplot;