import React from 'react';
import { ResponsiveContainer, Tooltip, Legend } from 'recharts';
import ChartTooltip from './ChartTooltip';
import ChartLegend from './ChartLegend';
import { gridColors } from './colors';

/**
 * Base chart wrapper component that provides responsive container,
 * consistent styling, and optional loading/error/empty states.
 *
 * All chart components should use this wrapper for consistent behavior.
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Chart component(s) to render
 * @param {number|string} props.width - Container width (default: '100%')
 * @param {number|string} props.height - Container height (default: 400)
 * @param {number} props.minWidth - Minimum width in pixels
 * @param {number} props.minHeight - Minimum height in pixels
 * @param {string} props.className - Additional CSS class names for outer wrapper
 * @param {string} props.title - Optional chart title
 * @param {string} props.subtitle - Optional chart subtitle
 * @param {boolean} props.loading - Show loading state
 * @param {string} props.error - Error message to display
 * @param {boolean} props.empty - Show empty state
 * @param {string} props.emptyMessage - Custom empty state message
 * @param {React.ReactNode} props.header - Custom header content
 * @param {React.ReactNode} props.footer - Custom footer content
 */
function BaseChart({
  children,
  width = '100%',
  height = 400,
  minWidth,
  minHeight,
  className = '',
  title,
  subtitle,
  loading = false,
  error = null,
  empty = false,
  emptyMessage = 'No data available',
  header,
  footer,
}) {
  // Loading state
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="animate-pulse">
          {(title || header) && <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />}
          <div className="h-64 bg-gray-100 rounded" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg ${className}`}>
        <p className="font-medium">Error loading chart</p>
        <p className="text-sm mt-1">{error}</p>
      </div>
    );
  }

  // Empty state
  if (empty) {
    return (
      <div className={`bg-gray-50 border border-gray-200 p-6 rounded-lg text-center ${className}`}>
        <p className="text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {/* Header */}
      {(title || subtitle || header) && (
        <div className="mb-4">
          {header || (
            <>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-500">{subtitle}</p>
              )}
            </>
          )}
        </div>
      )}

      {/* Chart */}
      <div className="chart-container">
        <ResponsiveContainer
          width={width}
          height={height}
          minWidth={minWidth}
          minHeight={minHeight}
        >
          {children}
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      {footer && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          {footer}
        </div>
      )}
    </div>
  );
}

/**
 * Common axis configuration for consistent chart styling.
 */
export const defaultAxisConfig = {
  tick: { fontSize: 12, fill: gridColors.text },
  axisLine: { stroke: gridColors.line },
  tickLine: { stroke: gridColors.line },
};

/**
 * Common CartesianGrid configuration.
 */
export const defaultGridConfig = {
  strokeDasharray: '3 3',
  stroke: gridColors.line,
  vertical: false,
};

/**
 * Common chart margin configuration.
 */
export const defaultMargin = {
  top: 20,
  right: 30,
  left: 20,
  bottom: 5,
};

/**
 * Create common X-axis props with currency formatting.
 */
export function createCurrencyAxisProps(options = {}) {
  return {
    ...defaultAxisConfig,
    tickFormatter: (value) => {
      if (Math.abs(value) >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      }
      if (Math.abs(value) >= 1000) {
        return `$${(value / 1000).toFixed(0)}k`;
      }
      return `$${value}`;
    },
    ...options,
  };
}

/**
 * Create common axis props with percentage formatting.
 */
export function createPercentAxisProps(options = {}) {
  return {
    ...defaultAxisConfig,
    tickFormatter: (value) => `${value}%`,
    ...options,
  };
}

/**
 * Create common axis props with month/year formatting.
 */
export function createTimeAxisProps(options = {}) {
  return {
    ...defaultAxisConfig,
    tickFormatter: (month) => {
      if (month === 0) return '0';
      if (month % 12 === 0) return `${month / 12}yr`;
      return `${month}mo`;
    },
    ...options,
  };
}

export { ChartTooltip, ChartLegend };
export default BaseChart;
