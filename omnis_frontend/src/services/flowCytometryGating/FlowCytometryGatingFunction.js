/**
 * Utility functions for Flow Cytometry Gating
 */

/**
 * Check if a point is inside a polygon using the Ray Casting algorithm
 * @param {Object} point - The point to check {x, y}
 * @param {Array} polygon - Array of polygon vertices [{x, y}, ...]
 * @returns {boolean} True if the point is inside the polygon
 */
export function isPointInPolygon(point, polygon) {
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const xi = polygon[i].x;
      const yi = polygon[i].y;
      const xj = polygon[j].x;
      const yj = polygon[j].y;
  
      const intersect =
        yi > point.y !== yj > point.y &&
        point.x <
          ((xj - xi) * (point.y - yi)) / (yj - yi) + xi;
      if (intersect) inside = !inside;
    }
    return inside;
  }
  
  /**
   * Filter data points based on a polygon gate
   * @param {Array} dataPoints - Array of data points [{x, y}, ...]
   * @param {Array} polygon - Array of polygon vertices [{x, y}, ...]
   * @returns {Array} Filtered data points inside the polygon
   */
  export function filterPointsByGate(dataPoints, polygon) {
    return dataPoints.filter(point => isPointInPolygon(point, polygon));
  }
  
  /**
   * Convert screen (pixel) coordinates to data coordinates using scales
   * @param {Object} point - Screen coordinates {x, y}
   * @param {Function} xScale - D3 x scale function
   * @param {Function} yScale - D3 y scale function
   * @returns {Object} Data coordinates {x, y}
   */
  export function screenToDataCoordinates(point, xScale, yScale) {
    return {
      x: xScale.invert(point.x),
      y: yScale.invert(point.y)
    };
  }
  
  /**
   * Format gate data for API submission
   * @param {Array} vertices - Array of vertices in data coordinates [{x, y}, ...]
   * @param {string} gateName - Name of the gate
   * @returns {Object} Formatted gate data
   */
  export function formatGateData(vertices, gateName) {
    return {
      name: gateName,
      type: 'polygon',
      vertices: vertices.map(v => ({
        parameter1: v.x,
        parameter2: v.y
      }))
    };
  }
  
  export default {
    isPointInPolygon,
    filterPointsByGate,
    screenToDataCoordinates,
    formatGateData
  };