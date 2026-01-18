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
 * Custom tooltip for the savings impact chart.
 */
function SavingsTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const data = payload[0]?.payload;
  if (!data) return null;

  const isPositive = data.cumulative_savings >= 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-xs">
      <p className="text-sm font-semibold text-gray-900 mb-1">
        Month {data.month}
      </p>
      <p className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        Cumulative Savings:{' '}
        <span className="font-medium">
          {data.cumulative_savings >= 0 ? '+' : ''}
          ${data.cumulative_savings.toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
      </p>
      <p className="text-sm text-gray-600">
        Monthly Savings:{' '}
        <span className="font-medium">
          ${data.monthly_diff.toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
      </p>
    </div>
  );
}

/**
 * Summary card showing key refinance metrics.
 */
function SavingsSummary({ summary }) {
  if (!summary) return null;

  const formatCurrency = (value) =>
    `$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

  const formatRate = (value) =>
    `${(value * 100).toFixed(2)}%`;

  const items = [
    {
      label: 'Current Payment',
      value: formatCurrency(summary.current_payment),
      color: 'text-gray-900',
    },
    {
      label: 'Refi Payment',
      value: formatCurrency(summary.refi_payment),
      color: 'text-blue-600',
    },
    {
      label: 'Monthly Savings',
      value: formatCurrency(summary.monthly_savings),
      color: summary.monthly_savings > 0 ? 'text-green-600' : 'text-red-600',
    },
    {
      label: 'Break-even',
      value: summary.breakeven_month
        ? `${summary.breakeven_month} months`
        : 'N/A',
      color: 'text-amber-600',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
      {items.map((item) => (
        <div key={item.label} className="text-center">
          <p className="text-xs text-gray-500 uppercase tracking-wide">
            {item.label}
          </p>
          <p className={`text-lg font-semibold ${item.color}`}>{item.value}</p>
        </div>
      ))}
    </div>
  );
}

/**
 * SavingsImpactChart component showing refinance savings comparison.
 *
 * Displays an interactive chart with:
 * - Cumulative savings over time (area chart)
 * - Break-even point reference line
 * - Summary metrics for quick comparison
 *
 * @param {Object} props
 * @param {number} props.mortgageId - Optional mortgage ID to fetch data for
 * @param {number} props.targetRate - Optional target refinance rate
 * @param {number} props.targetTerm - Optional target refinance term
 * @param {number} props.refiCost - Optional refinance closing costs
 * @param {Object} props.initialData - Optional initial data to display before fetch
 * @param {number} props.height - Chart height in pixels (default: 400)
 */
function SavingsImpactChart({
  mortgageId,
  targetRate,
  targetTerm,
  refiCost,
  initialData,
  height = 400,
}) {
  const [data, setData] = useState(initialData || null);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchSavingsImpact() {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        if (mortgageId) params.append('mortgage_id', mortgageId);
        if (targetRate) params.append('target_rate', targetRate);
        if (targetTerm) params.append('target_term', targetTerm);
        if (refiCost) params.append('refi_cost', refiCost);

        const url = `/api/savings-impact${params.toString() ? `?${params}` : ''}`;
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch savings impact data');
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
      fetchSavingsImpact();
    }
  }, [mortgageId, targetRate, targetTerm, refiCost, initialData]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
          <div className="grid grid-cols-4 gap-4 mb-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-12 bg-gray-100 rounded" />
            ))}
          </div>
          <div className="h-64 bg-gray-100 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
        Error loading savings impact: {error}
      </div>
    );
  }

  if (!data || !data.savings_data?.length) {
    return (
      <div className="bg-gray-50 border border-gray-200 p-6 rounded-lg text-center">
        <p className="text-gray-500">No savings data available yet.</p>
        <p className="text-sm text-gray-400 mt-1">
          Add a mortgage to see potential refinance savings.
        </p>
      </div>
    );
  }

  const { savings_data, summary } = data;

  // Sample data for better chart performance (every 6 months)
  const sampledData = savings_data.filter(
    (d, i) => i === 0 || i === savings_data.length - 1 || i % 6 === 0
  );

  // Calculate Y-axis domain
  const allValues = savings_data.map((d) => d.cumulative_savings);
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const padding = Math.abs(maxValue - minValue) * 0.1;
  const yMin = Math.floor((minValue - padding) / 1000) * 1000;
  const yMax = Math.ceil((maxValue + padding) / 1000) * 1000;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Savings Impact Analysis
        </h3>
        {data.mortgage_name && (
          <p className="text-sm text-gray-500">{data.mortgage_name}</p>
        )}
      </div>

      <SavingsSummary summary={summary} />

      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart
          data={sampledData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12 }}
            tickFormatter={(month) => {
              if (month === 0) return '0';
              if (month % 12 === 0) return `${month / 12}yr`;
              return `${month}mo`;
            }}
            label={{
              value: 'Time After Refinance',
              position: 'insideBottom',
              offset: -5,
              fontSize: 12,
            }}
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => {
              if (Math.abs(v) >= 1000) {
                return `$${(v / 1000).toFixed(0)}k`;
              }
              return `$${v}`;
            }}
            label={{
              value: 'Cumulative Savings',
              angle: -90,
              position: 'insideLeft',
              fontSize: 12,
            }}
          />
          <Tooltip content={<SavingsTooltip />} />
          <Legend verticalAlign="top" height={36} />

          {/* Zero reference line */}
          <ReferenceLine
            y={0}
            stroke="#9ca3af"
            strokeWidth={1}
          />

          {/* Break-even reference line */}
          {summary?.breakeven_month && (
            <ReferenceLine
              x={summary.breakeven_month}
              stroke="#f59e0b"
              strokeDasharray="8 4"
              strokeWidth={2}
              label={{
                value: `Break-even: ${summary.breakeven_month} mo`,
                fill: '#f59e0b',
                fontSize: 11,
                position: 'top',
              }}
            />
          )}

          {/* Negative savings area (loss) */}
          <Area
            type="monotone"
            dataKey="cumulative_savings"
            stroke="none"
            fill="#fecaca"
            fillOpacity={0.5}
            name="Loss Period"
            legendType="none"
            baseValue={0}
            isAnimationActive={true}
          />

          {/* Cumulative savings line */}
          <Line
            type="monotone"
            dataKey="cumulative_savings"
            stroke="#16a34a"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6, fill: '#16a34a' }}
            name="Cumulative Savings"
          />
        </ComposedChart>
      </ResponsiveContainer>

      {summary && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-sm text-gray-600">
            <span className="font-medium">Rate comparison:</span>{' '}
            {(summary.current_rate * 100).toFixed(2)}% (current) vs{' '}
            {(summary.target_rate * 100).toFixed(2)}% (target) |{' '}
            <span className="font-medium">Closing costs:</span>{' '}
            ${summary.refi_cost.toLocaleString()}
            {summary.total_savings_at_term > 0 && (
              <>
                {' '}|{' '}
                <span className="font-medium text-green-600">
                  Total savings over term: ${summary.total_savings_at_term.toLocaleString()}
                </span>
              </>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

export default SavingsImpactChart;
