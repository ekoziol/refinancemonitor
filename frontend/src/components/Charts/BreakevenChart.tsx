import { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Label,
  Legend,
} from 'recharts';

export interface BreakevenData {
  month: number;
  simpleSavings: number;
  interestSavings: number;
}

export interface BreakevenChartProps {
  data: BreakevenData[];
}

/**
 * Break-even Analysis Chart
 *
 * Displays dual break-even analysis for refinancing:
 * 1. Simple method (blue): Monthly payment savings accumulation
 * 2. Interest-only method (green): Total interest comparison
 *
 * The chart shows when refinancing costs are recouped through savings.
 */
export function BreakevenChart({ data }: BreakevenChartProps) {
  // Find break-even points (where savings cross from negative to positive)
  const simpleBreakevenMonth = useMemo(() => {
    for (let i = 1; i < data.length; i++) {
      if (data[i - 1].simpleSavings <= 0 && data[i].simpleSavings > 0) {
        // Linear interpolation to find exact month
        const prev = data[i - 1];
        const curr = data[i];
        const ratio = -prev.simpleSavings / (curr.simpleSavings - prev.simpleSavings);
        return Math.round(prev.month + ratio * (curr.month - prev.month));
      }
    }
    // Check if already positive at start
    if (data.length > 0 && data[0].simpleSavings > 0) return 0;
    return null;
  }, [data]);

  const interestBreakevenMonth = useMemo(() => {
    for (let i = 1; i < data.length; i++) {
      if (data[i - 1].interestSavings <= 0 && data[i].interestSavings > 0) {
        // Linear interpolation to find exact month
        const prev = data[i - 1];
        const curr = data[i];
        const ratio = -prev.interestSavings / (curr.interestSavings - prev.interestSavings);
        return Math.round(prev.month + ratio * (curr.month - prev.month));
      }
    }
    // Check if already positive at start
    if (data.length > 0 && data[0].interestSavings > 0) return 0;
    return null;
  }, [data]);

  // Calculate Y-axis bounds
  const { yMin, yMax } = useMemo(() => {
    if (data.length === 0) return { yMin: -10000, yMax: 10000 };
    const allValues = data.flatMap((d) => [d.simpleSavings, d.interestSavings]);
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    // Add padding
    const padding = (max - min) * 0.1 || 1000;
    return { yMin: min - padding, yMax: max + padding };
  }, [data]);

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Custom tooltip content
  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{ payload: BreakevenData; dataKey: string; color: string }>;
  }) => {
    if (active && payload && payload.length > 0) {
      const point = payload[0].payload;
      return (
        <div className="bg-white border border-gray-200 rounded shadow-lg p-3">
          <p className="font-medium">Month {point.month}</p>
          <p className="text-blue-600">
            Simple Savings: {formatCurrency(point.simpleSavings)}
          </p>
          <p className="text-green-600">
            Interest Savings: {formatCurrency(point.interestSavings)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div
      className="w-full"
      role="img"
      aria-label="Break-even Analysis Chart showing refinancing savings over time"
    >
      <h3 className="text-center font-semibold text-gray-800 mb-4">
        Breakeven Point
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <XAxis
            dataKey="month"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickLine={false}
          >
            <Label
              value="Months After Refinance Occurs"
              position="bottom"
              offset={20}
              style={{ fill: '#374151', fontSize: 12 }}
            />
          </XAxis>
          <YAxis
            domain={[yMin, yMax]}
            tickFormatter={formatCurrency}
            tickLine={false}
          >
            <Label
              value="Amount Saved"
              angle={-90}
              position="insideLeft"
              style={{ textAnchor: 'middle', fill: '#374151', fontSize: 12 }}
            />
          </YAxis>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            wrapperStyle={{ paddingTop: '20px' }}
          />

          {/* Zero line (break-even threshold) */}
          <ReferenceLine
            y={0}
            stroke="#000000"
            strokeWidth={1}
          />

          {/* Simple method break-even vertical line */}
          {simpleBreakevenMonth !== null && (
            <ReferenceLine
              x={simpleBreakevenMonth}
              stroke="#3b82f6"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: `Simple: ${simpleBreakevenMonth} mo`,
                position: 'top',
                fill: '#3b82f6',
                fontSize: 10,
              }}
            />
          )}

          {/* Interest method break-even vertical line */}
          {interestBreakevenMonth !== null && (
            <ReferenceLine
              x={interestBreakevenMonth}
              stroke="#22c55e"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: `Interest: ${interestBreakevenMonth} mo`,
                position: 'insideTopRight',
                fill: '#22c55e',
                fontSize: 10,
              }}
            />
          )}

          {/* Simple savings line (blue) */}
          <Line
            type="monotone"
            dataKey="simpleSavings"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Simple Savings"
          />

          {/* Interest savings line (green) */}
          <Line
            type="monotone"
            dataKey="interestSavings"
            stroke="#22c55e"
            strokeWidth={2}
            dot={false}
            name="Interest Savings"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Break-even summary */}
      <div className="flex justify-center gap-8 mt-2 text-sm text-gray-600">
        <div className="flex items-center">
          <span
            className="inline-block w-3 h-3 rounded-full mr-2"
            style={{ backgroundColor: '#3b82f6' }}
          />
          <span>
            Monthly Savings Break-even:{' '}
            {simpleBreakevenMonth !== null ? `${simpleBreakevenMonth} months` : 'Not reached'}
          </span>
        </div>
        <div className="flex items-center">
          <span
            className="inline-block w-3 h-3 rounded-full mr-2"
            style={{ backgroundColor: '#22c55e' }}
          />
          <span>
            Interest Savings Break-even:{' '}
            {interestBreakevenMonth !== null ? `${interestBreakevenMonth} months` : 'Not reached'}
          </span>
        </div>
      </div>
    </div>
  );
}
