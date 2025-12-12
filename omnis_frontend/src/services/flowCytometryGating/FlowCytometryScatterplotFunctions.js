/**
 * Calculates the density of each point based on a grid.
 * @param {Array} data - The array of data points.
 * @param {Function} xScale - D3 scale for the x-axis.
 * @param {Function} yScale - D3 scale for the y-axis.
 * @param {number} width - Width of the plot.
 * @param {number} height - Height of the plot.
 * @param {number} bins - Number of bins for both axes.
 * @returns {Array} - Array of density values corresponding to each data point.
 */

export function calculateDensity(data, xScale, yScale, width, height, bins=150){
    // initialize the grid for the density
    const grid = Array.from({length: bins}, () => Array(bins).fill(0));

    // assign points to grid cells
    data.forEach(point => {
        // set x and y to the grid cell coordinates
        const x = xScale(point.x);
        const y = yScale(point.y);

        // get binX and binY
        const binX = Math.min(Math.floor((x / width) * bins), bins - 1);
        const binY = Math.min(Math.floor(((height - y) / height) * bins), bins - 1);

        // check if the point is in the grid
        if (binX >= 0 && binX < bins && binY >= 0  && binY < bins){
            grid[binY][binX]+=1;
        }
    });
    
    // calculate the maximum density from the grid with the flat() method to flatten the grid into a 1D array
    const maxDensity = Math.max(...grid.flat());

    // calculate the density for each point
    const densities = data.map(point =>{
        const x = xScale(point.x);
        const y = yScale(point.y);

        const binX = Math.min(Math.floor((x / width) * bins), bins - 1);
        const binY = Math.min(Math.floor(((height - y) / height) * bins), bins - 1);

        if (binX >= 0 && binX < bins && binY >= 0 && binY < bins){
            return grid[binY][binX]/maxDensity;
        }
        return 0;
    });
    console.log('Grid:', grid);
    console.log('Max Density:', maxDensity);
    console.log('Densities:', densities);
    return densities;
}