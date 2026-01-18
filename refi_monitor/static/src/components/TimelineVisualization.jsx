import React, { useState, useEffect } from 'react';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';

/**
 * Custom tooltip for the timeline chart showing event details.
 */
function TimelineTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const data = payload[0]?.payload;
  if (!data) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-xs">
      <p className="text-sm font-semibold text-gray-900 mb-1">
        {new Date(data.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}
      </p>
      {data.rate !== undefined && (
        <p className="text-sm text-gray-600">
          Rate: <span className="font-medium">{data.rate.toFixed(2)}%</span>
        </p>
      )}
      {data.forecastRate !== undefined && (
        <p className="text-sm text-blue-600">
          Forecast: <span className="font-medium">{data.forecastRate.toFixed(2)}%</span>
        </p>
      )}
      {data.eventType && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${getEventBadgeClass(data.eventType)}`}>
            {data.eventLabel}
          </span>
          {data.eventDescription && (
            <p className="text-xs text-gray-500 mt-1">{data.eventDescription}</p>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Get badge color class based on event type.
 */
function getEventBadgeClass(eventType) {
  switch (eventType) {
    case 'mortgage_created':
      return 'bg-purple-100 text-purple-800';
    case 'alert_created':
      return 'bg-blue-100 text-blue-800';
    case 'trigger':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Custom dot renderer for event markers on the chart.
 */
function EventDot({ cx, cy, payload }) {
  if (!payload.eventType || cx === undefined || cy === undefined) {
    return null;
  }

  const colors = {
    mortgage_created: '#9333ea',
    alert_created: '#2563eb',
    trigger: '#16a34a',
  };

  const color = colors[payload.eventType] || '#6b7280';

  return (
    <g>
      <circle cx={cx} cy={cy} r={8} fill={color} fillOpacity={0.2} />
      <circle cx={cx} cy={cy} r={5} fill={color} />
    </g>
  );
}

/**
 * Legend item for event types.
 */
function EventLegend() {
  const items = [
    { type: 'mortgage_created', label: 'Mortgage Created', color: '#9333ea' },
    { type: 'alert_created', label: 'Alert Set', color: '#2563eb' },
    { type: 'trigger', label: 'Rate Target Met', color: '#16a34a' },
  ];

  return (
    <div className="flex flex-wrap justify-center gap-4 mt-2 text-sm">
      {items.map((item) => (
        <div key={item.type} className="flex items-center gap-1.5">
          <span
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-gray-600">{item.label}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * TimelineVisualization component showing mortgage events and rate forecast.
 *
 * Displays an interactive timeline chart with:
 * - Historical mortgage rate data (solid line)
 * - Rate forecast with confidence interval (dashed line with shaded area)
 * - Event markers for mortgage creation, alerts, and triggers
 * - Target rate reference line if an alert is active
 *
 * @param {Object} props
 * @param {number} props.mortgageId - Optional mortgage ID to fetch data for
 * @param {Object} props.initialData - Optional initial data to display before fetch
 * @param {number} props.height - Chart height in pixels (default: 400)
 */
function TimelineVisualization({ mortgageId, initialData, height = 400 }) {
  const [data, setData] = useState(initialData || null);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchTimeline() {
      try {
        setLoading(true);
        const url = mortgageId
          ? `/api/timeline?mortgage_id=${mortgageId}`
          : '/api/timeline';
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch timeline data');
        }
        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (!initialData) {
      fetchTimeline();
    }
  }, [mortgageId, initialData]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
          <div className="h-64 bg-gray-100 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
        Error loading timeline: {error}
      </div>
    );
  }

  if (!data || (!data.rate_history?.length && !data.events?.length)) {
    return (
      <div className="bg-gray-50 border border-gray-200 p-6 rounded-lg text-center">
        <p className="text-gray-500">No timeline data available yet.</p>
        <p className="text-sm text-gray-400 mt-1">
          Rate data and events will appear here as they are recorded.
        </p>
      </div>
    );
  }

  // Merge rate history, forecast, and events into unified chart data
  const chartData = [];
  const eventsByDate = {};

  // Index events by date
  data.events?.forEach((event) => {
    eventsByDate[event.date] = event;
  });

  // Add historical rate data points
  data.rate_history?.forEach((point) => {
    const event = eventsByDate[point.date];
    chartData.push({
      date: point.date,
      rate: point.rate,
      eventType: event?.type,
      eventLabel: event?.label,
      eventDescription: event?.description,
    });
  });

  // Add forecast data points
  data.forecast?.forEach((point) => {
    const event = eventsByDate[point.date];
    chartData.push({
      date: point.date,
      forecastRate: point.rate,
      upper: point.upper,
      lower: point.lower,
      eventType: event?.type,
      eventLabel: event?.label,
      eventDescription: event?.description,
    });
  });

  // Add any events not on rate data dates
  data.events?.forEach((event) => {
    const exists = chartData.some((d) => d.date === event.date);
    if (!exists) {
      chartData.push({
        date: event.date,
        eventType: event.type,
        eventLabel: event.label,
        eventDescription: event.description,
      });
    }
  });

  // Sort by date
  chartData.sort((a, b) => new Date(a.date) - new Date(b.date));

  // Calculate Y-axis domain
  const allRates = chartData
    .flatMap((d) => [d.rate, d.forecastRate, d.upper, d.lower])
    .filter((v) => v !== undefined);
  const minRate = Math.floor(Math.min(...allRates) - 0.5);
  const maxRate = Math.ceil(Math.max(...allRates) + 0.5);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Rate Timeline & Forecast
        </h3>
        {data.mortgage_name && (
          <p className="text-sm text-gray-500">{data.mortgage_name}</p>
        )}
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(date) =>
              new Date(date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              })
            }
          />
          <YAxis
            domain={[minRate, maxRate]}
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip content={<TimelineTooltip />} />
          <Legend
            verticalAlign="top"
            height={36}
            formatter={(value) => {
              const labels = {
                rate: 'Historical Rate',
                forecastRate: 'Forecast',
              };
              return labels[value] || value;
            }}
          />

          {/* Confidence interval area */}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="#dbeafe"
            fillOpacity={0.5}
            name="upper"
            legendType="none"
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#ffffff"
            fillOpacity={1}
            name="lower"
            legendType="none"
          />

          {/* Historical rate line */}
          <Line
            type="monotone"
            dataKey="rate"
            stroke="#2563eb"
            strokeWidth={2}
            dot={<EventDot />}
            activeDot={{ r: 6, fill: '#2563eb' }}
            name="rate"
          />

          {/* Forecast line */}
          <Line
            type="monotone"
            dataKey="forecastRate"
            stroke="#dc2626"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="forecastRate"
          />

          {/* Target rate reference line */}
          {data.target_rate && (
            <ReferenceLine
              y={data.target_rate}
              stroke="#f59e0b"
              strokeDasharray="8 4"
              strokeWidth={2}
              label={{
                value: `Target: ${data.target_rate}%`,
                fill: '#f59e0b',
                fontSize: 12,
                position: 'right',
              }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      <EventLegend />
    </div>
  );
}

export default TimelineVisualization;
