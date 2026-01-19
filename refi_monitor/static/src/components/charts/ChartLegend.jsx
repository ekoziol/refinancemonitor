import React from 'react';

/**
 * Reusable chart legend component for Recharts.
 *
 * Provides a customizable legend that can be used standalone or with Recharts'
 * Legend component via the content prop.
 *
 * @param {Object} props
 * @param {Array} props.payload - Legend payload from Recharts
 * @param {string} props.align - Horizontal alignment: 'left', 'center', 'right'
 * @param {string} props.layout - Layout direction: 'horizontal', 'vertical'
 * @param {Object} props.labels - Custom labels map { dataKey: 'Display Name' }
 * @param {Function} props.onClick - Optional click handler for legend items
 * @param {Array} props.hiddenItems - Array of dataKeys to show as hidden/inactive
 * @param {string} props.iconType - Icon shape: 'circle', 'square', 'line'
 */
function ChartLegend({
  payload,
  align = 'center',
  layout = 'horizontal',
  labels = {},
  onClick,
  hiddenItems = [],
  iconType = 'circle',
}) {
  if (!payload || !payload.length) {
    return null;
  }

  const alignmentClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
  };

  const layoutClasses = {
    horizontal: 'flex-row flex-wrap',
    vertical: 'flex-col',
  };

  const renderIcon = (color, type) => {
    const baseClasses = 'flex-shrink-0';

    switch (type) {
      case 'square':
        return (
          <span
            className={`${baseClasses} w-3 h-3 rounded-sm`}
            style={{ backgroundColor: color }}
          />
        );
      case 'line':
        return (
          <span
            className={`${baseClasses} w-4 h-0.5 rounded`}
            style={{ backgroundColor: color }}
          />
        );
      case 'circle':
      default:
        return (
          <span
            className={`${baseClasses} w-3 h-3 rounded-full`}
            style={{ backgroundColor: color }}
          />
        );
    }
  };

  return (
    <div
      className={`flex gap-4 py-2 text-sm ${alignmentClasses[align]} ${layoutClasses[layout]}`}
    >
      {payload.map((entry, index) => {
        // Skip hidden legend entries
        if (entry.type === 'none' || entry.legendType === 'none') {
          return null;
        }

        const isHidden = hiddenItems.includes(entry.dataKey || entry.value);
        const displayName = labels[entry.dataKey || entry.value] || entry.value;
        const color = isHidden ? '#d1d5db' : entry.color;

        return (
          <button
            key={`legend-${index}`}
            type="button"
            className={`flex items-center gap-1.5 transition-opacity ${
              isHidden ? 'opacity-50' : 'opacity-100'
            } ${onClick ? 'cursor-pointer hover:opacity-75' : 'cursor-default'}`}
            onClick={() => onClick && onClick(entry, index)}
            disabled={!onClick}
          >
            {renderIcon(color, iconType)}
            <span className={`text-gray-600 ${isHidden ? 'line-through' : ''}`}>
              {displayName}
            </span>
          </button>
        );
      })}
    </div>
  );
}

/**
 * Create a configured legend component with preset options.
 *
 * @param {Object} config - Legend configuration
 * @returns {Function} Configured legend component
 */
export function createLegend(config) {
  return function ConfiguredLegend(props) {
    return <ChartLegend {...props} {...config} />;
  };
}

/**
 * Simple inline legend for use outside of Recharts.
 *
 * @param {Object} props
 * @param {Array} props.items - Array of { label, color } objects
 * @param {string} props.align - Horizontal alignment
 * @param {string} props.iconType - Icon shape
 */
export function SimpleLegend({ items, align = 'center', iconType = 'circle' }) {
  const payload = items.map((item) => ({
    value: item.label,
    color: item.color,
    dataKey: item.label,
  }));

  return <ChartLegend payload={payload} align={align} iconType={iconType} />;
}

export default ChartLegend;
