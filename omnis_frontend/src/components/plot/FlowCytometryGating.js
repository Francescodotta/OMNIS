import React, { useEffect, useRef, useState } from 'react';
import flowCytometryApi from '../../utils/ApiFlowCytometry';
import * as d3 from 'd3';

const FlowCytometryPlot = ({ username, projectId, progressiveId, gatingStrategyId }) => {
  const [data, setData] = useState([]);
  const svgRef = useRef();
  console.log('gatingStrategyId:', gatingStrategyId);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await flowCytometryApi.get(`/flow_cytometry/api/v1/project/${projectId}/fcs_object/${progressiveId}/gating_strategies/${gatingStrategyId}/gating_elements`);
        setData(response.data);
        console.log('Data:', response.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, [username, projectId, progressiveId, gatingStrategyId]);

  useEffect(() => {
    if (data.length > 0) {
      const svg = d3.select(svgRef.current);
      svg.selectAll('*').remove(); // Clear previous content

      const width = 800;
      const height = 600;
      const margin = { top: 20, right: 30, bottom: 40, left: 50 };

      // Approximate a logicle transformation using D3's symlog scale.
      // The symlog scale is nearly linear close to zero (handling negative values)
      // and logarithmic further away; adjust the constant for the linearization region.
      const cofactor = 150; // You can adjust this to fit your data's dynamic range
      const x = d3.scaleSymlog()
        .constant(cofactor)
        .domain(d3.extent(data, d => d['parameter1']))
        .range([margin.left, width - margin.right]);

      const y = d3.scaleSymlog()
        .constant(cofactor)
        .domain(d3.extent(data, d => d['parameter2']))
        .range([height - margin.bottom, margin.top]);

      // Draw the x-axis
      svg.append('g')
        .attr('transform', `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x));

      // Draw the y-axis
      svg.append('g')
        .attr('transform', `translate(${margin.left},0)`)
        .call(d3.axisLeft(y));

      // Plot data points using the transformed scales
      svg.append('g')
        .selectAll('circle')
        .data(data)
        .enter()
        .append('circle')
        .attr('cx', d => x(d['parameter1'])) // Replace 'parameter1' with your actual parameter
        .attr('cy', d => y(d['parameter2'])) // Replace 'parameter2' with your actual parameter
        .attr('r', 3)
        .attr('fill', 'steelblue');
    }
  }, [data]);

  return (
    <div>
      <svg ref={svgRef} width={800} height={600}></svg>
    </div>
  );
};

export default FlowCytometryPlot;