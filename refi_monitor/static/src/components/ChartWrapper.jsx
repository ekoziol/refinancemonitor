import React from 'react';
import { ResponsiveContainer } from 'recharts';

/**
 * Base chart wrapper component that provides responsive container functionality.
 * All chart components should be wrapped with this to ensure proper responsive behavior.
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Chart component(s) to render
 * @param {number|string} props.width - Container width (default: '100%')
 * @param {number|string} props.height - Container height (default: 400)
 * @param {number} props.minWidth - Minimum width in pixels
 * @param {number} props.minHeight - Minimum height in pixels
 * @param {string} props.className - Additional CSS class names
 */
function ChartWrapper({
  children,
  width = '100%',
  height = 400,
  minWidth,
  minHeight,
  className = '',
}) {
  return (
    <div className={`chart-wrapper ${className}`}>
      <ResponsiveContainer
        width={width}
        height={height}
        minWidth={minWidth}
        minHeight={minHeight}
      >
        {children}
      </ResponsiveContainer>
    </div>
  );
}

export default ChartWrapper;
