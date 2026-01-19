import React from 'react';
import { semanticColors } from './colors';

/**
 * Format a value for display in tooltips.
 * @param {number} value - The value to format
 * @param {string} format - Format type: 'currency', 'percent', 'number', 'compact'
 * @param {Object} options - Additional formatting options
 * @returns {string} Formatted value
 */
export function formatTooltipValue(value, format = 'number', options = {}) {
  if (value === null || value === undefined) return 'N/A';

  const { decimals = 2, prefix = '', suffix = '' } = options;

  switch (format) {
    case 'currency':
      return `${prefix}$${value.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}${suffix}`;

    case 'percent':
      return `${prefix}${value.toFixed(decimals)}%${suffix}`;

    case 'compact':
      if (Math.abs(value) >= 1000000) {
        return `${prefix}$${(value / 1000000).toFixed(1)}M${suffix}`;
      }
      if (Math.abs(value) >= 1000) {
        return `${prefix}$${(value / 1000).toFixed(1)}k${suffix}`;
      }
      return `${prefix}$${value.toFixed(0)}${suffix}`;

    case 'number':
    default:
      return `${prefix}${value.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}${suffix}`;
  }
}

/**
 * Reusable chart tooltip component for Recharts.
 *
 * @param {Object} props - Recharts tooltip props
 * @param {boolean} props.active - Whether tooltip is active
 * @param {Array} props.payload - Data payload from Recharts
 * @param {string} props.label - X-axis label
 * @param {Function} props.labelFormatter - Custom label formatter
 * @param {Function} props.valueFormatter - Custom value formatter
 * @param {Object} props.dataKeyLabels - Map of dataKey to display label
 * @param {Object} props.dataKeyFormats - Map of dataKey to format type
 * @param {string} props.title - Optional tooltip title
 * @param {React.ReactNode} props.footer - Optional footer content
 */
function ChartTooltip({
  active,
  payload,
  label,
  labelFormatter,
  valueFormatter,
  dataKeyLabels = {},
  dataKeyFormats = {},
  title,
  footer,
}) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const formattedLabel = labelFormatter ? labelFormatter(label, payload) : label;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-xs">
      {(title || formattedLabel) && (
        <p className="text-sm font-semibold text-gray-900 mb-2">
          {title || formattedLabel}
        </p>
      )}

      <div className="space-y-1">
        {payload.map((entry, index) => {
          // Skip entries with undefined values or legend-only entries
          if (entry.value === undefined || entry.legendType === 'none') {
            return null;
          }

          const displayName = dataKeyLabels[entry.dataKey] || entry.name || entry.dataKey;
          const format = dataKeyFormats[entry.dataKey] || 'number';
          const formattedValue = valueFormatter
            ? valueFormatter(entry.value, entry.dataKey, entry)
            : formatTooltipValue(entry.value, format);

          // Determine color based on value if positive/negative coloring is needed
          const isPositiveFormat = format === 'currency' || format === 'compact';
          const valueColor = isPositiveFormat && entry.value < 0
            ? semanticColors.negative
            : entry.color || semanticColors.neutral;

          return (
            <div key={`${entry.dataKey}-${index}`} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-1.5">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: entry.color || valueColor }}
                />
                <span className="text-sm text-gray-600">{displayName}</span>
              </div>
              <span
                className="text-sm font-medium"
                style={{ color: valueColor }}
              >
                {formattedValue}
              </span>
            </div>
          );
        })}
      </div>

      {footer && (
        <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500">
          {footer}
        </div>
      )}
    </div>
  );
}

/**
 * Create a configured tooltip component with preset options.
 *
 * @param {Object} config - Tooltip configuration
 * @returns {Function} Configured tooltip component
 */
export function createTooltip(config) {
  return function ConfiguredTooltip(props) {
    return <ChartTooltip {...props} {...config} />;
  };
}

export default ChartTooltip;
