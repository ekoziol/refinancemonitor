/**
 * Chart color palette for Recharts.
 *
 * Colors are defined to match the CSS oklch variables but as hex values
 * for direct use in Recharts which doesn't support oklch.
 */

// Primary chart colors (1-5) matching --chart-1 through --chart-5
export const chartColors = {
  primary: '#4f6bed',    // chart-1: blue
  success: '#22c55e',    // chart-2: green
  orange: '#f97316',     // chart-3: orange
  pink: '#ec4899',       // chart-4: pink/magenta
  teal: '#14b8a6',       // chart-5: teal
};

// Ordered array for sequential data series
export const chartColorScale = [
  chartColors.primary,
  chartColors.success,
  chartColors.orange,
  chartColors.pink,
  chartColors.teal,
];

// Semantic colors for specific meanings
export const semanticColors = {
  positive: '#22c55e',    // green - gains, success
  negative: '#ef4444',    // red - losses, errors
  neutral: '#6b7280',     // gray - neutral values
  warning: '#f59e0b',     // amber - warnings, caution
  info: '#3b82f6',        // blue - informational
};

// Area fill colors (lighter versions for backgrounds)
export const areaColors = {
  primary: '#dbeafe',     // light blue
  success: '#dcfce7',     // light green
  negative: '#fecaca',    // light red
  orange: '#fed7aa',      // light orange
  pink: '#fce7f3',        // light pink
  teal: '#ccfbf1',        // light teal
};

// Grid and axis colors
export const gridColors = {
  line: '#e5e7eb',        // gray-200
  text: '#6b7280',        // gray-500
  axis: '#9ca3af',        // gray-400
};

// Reference line colors
export const referenceColors = {
  breakeven: '#f59e0b',   // amber for breakeven points
  target: '#16a34a',      // green for target lines
  current: '#2563eb',     // blue for current values
  zero: '#9ca3af',        // gray for zero line
};

/**
 * Get a color from the scale by index (wraps around if exceeded).
 * @param {number} index - The data series index
 * @returns {string} Hex color value
 */
export function getChartColor(index) {
  return chartColorScale[index % chartColorScale.length];
}

/**
 * Generate a color scale with a specific number of colors.
 * For more than 5 colors, interpolates additional values.
 * @param {number} count - Number of colors needed
 * @returns {string[]} Array of hex color values
 */
export function generateColorScale(count) {
  if (count <= chartColorScale.length) {
    return chartColorScale.slice(0, count);
  }
  // For larger scales, repeat the palette
  const colors = [];
  for (let i = 0; i < count; i++) {
    colors.push(chartColorScale[i % chartColorScale.length]);
  }
  return colors;
}
