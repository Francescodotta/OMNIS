/**
 * Defines various color scales for scatter plots.
 */

import * as d3 from 'd3';

/**
 * Creates an Enhanced JET-style color scale with blue -> cyan -> green -> yellow -> orange -> red.
 * @returns {Function} - D3 color scale function.
 */
export function jetColorScale() {
  return d3.scaleLinear()
    .domain([0, 0.2, 0.4, 0.6, 0.8, 1.0]) // Expanded domain for smoother transitions
    .range([
      "#00007F", // Dark Blue
      "#007FFF", // Cyan
      "#7FFF7F", // Green
      "#FFFF00", // Yellow
      "#FF7F00", // Orange
      "#FF0000"  // Red
    ])
    .interpolate(d3.interpolateRgb);
}