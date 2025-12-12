import * as d3 from 'd3';
import { screenToDataCoordinates } from './FlowCytometryGatingFunction';

/**
 * Attach a click handler to the overlay to handle polygon gating.
 *
 * @param {Object} params - Parameters for gating.
 * @param {Object} params.overlay - The D3 overlay element.
 * @param {Function} params.setGatingVertices - React state setter for data vertices.
 * @param {Function} params.setCurrentGateVertices - React state setter for data vertices.
 * @param {Function} params.completeGating - Function to call when a gate has been completed.
 * @param {Array} params.gatingVertices - Array of data coordinates for gating.
 * @param {Array} params.currentGateVertices - Array of data coordinates.
 * @param {Object} params.polygonLine - D3 element for the polygon (polyline).
 * @param {boolean} params.isGating - Whether gating mode is active.
 * @param {Object} params.gatingGroup - D3 group element where vertex dots are drawn.
 * @param {Function} params.xScale - D3 x scale.
 * @param {Function} params.yScale - D3 y scale.
 */
export const handleGatingClick = ({
  overlay,
  setGatingVertices,
  setCurrentGateVertices,
  completeGating,
  gatingVertices,
  currentGateVertices,
  polygonLine,
  isGating,
  gatingGroup,
  xScale,
  yScale,
}) => {
  overlay.on('click', function (event) {
    if (!isGating) return;

    // Get mouse coordinates relative to the overlay.
    const [mouseX, mouseY] = d3.pointer(event, this);
    console.log('Overlay click at (screen):', mouseX, mouseY);

    // Convert screen coordinates to real data coordinates.
    const dataCoords = screenToDataCoordinates({ x: mouseX, y: mouseY }, xScale, yScale);
    console.log('Converted data coordinates:', dataCoords);

    const threshold = 10; // pixels (threshold is still in screen space)
    if (gatingVertices.length > 0) {
      // Convert the first data vertex into screen coordinates for threshold check.
      const firstVertexScreen = {
        x: xScale(gatingVertices[0].x),
        y: yScale(gatingVertices[0].y)
      };
      const distToFirst = Math.hypot(mouseX - firstVertexScreen.x, mouseY - firstVertexScreen.y);
      if (gatingVertices.length >= 3 && distToFirst < threshold) {
        completeGating();
        return;
      }
    }

    // Save the real data coordinates.
    const newDataVertex = { x: dataCoords.x, y: dataCoords.y };

    const updatedGatingVertices = [...gatingVertices, newDataVertex];
    // For ease, we store the data vertices in both state variables.
    setGatingVertices(updatedGatingVertices);
    setCurrentGateVertices(updatedGatingVertices);

    // For drawing, convert data vertices into screen coordinates.
    polygonLine
      .attr('points', updatedGatingVertices.map(p => `${xScale(p.x)},${yScale(p.y)}`).join(' '))
      .style('visibility', 'visible');

    // Draw/update the vertex dots.
    const vertexDots = gatingGroup.selectAll('circle.gate-vertex')
      .data(updatedGatingVertices, d => `${d.x}-${d.y}`);

    // Append new dots.
    vertexDots.enter()
      .append('circle')
      .attr('class', 'gate-vertex')
      .attr('r', 6) // Increased radius for visibility.
      .attr('fill', 'red')
      .attr('stroke', 'black')
      .attr('stroke-width', 1)
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y));

    // Update positions for any existing dots.
    vertexDots
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y));

    vertexDots.exit().remove();

    console.log('Updated gating vertices (data coordinates):', updatedGatingVertices);
  });
};