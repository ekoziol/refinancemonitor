import { useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ReferenceDot,
  Label,
} from 'recharts';

export interface EfficientFrontierData {
  month: number;
  interestRate: number;
}

export interface EfficientFrontierChartProps {
  data: EfficientFrontierData[];
  currentMonth: number;
  targetRate: number;
}

/**
 * Efficient Frontier Chart
 *
 * Visualizes the break-even interest rate by month of the original loan.
 * Below the green line = paying less interest over the loan lifetime.
 * Above the green line = paying more interest over the loan lifetime.
 */
export function EfficientFrontierChart({
  data,
  currentMonth,
  targetRate,
}: EfficientFrontierChartProps) {
  // Find where interest rates go negative (break-even boundary)
  const negativeMonth = useMemo(() => {
    const firstNegative = data.find((d) => d.interestRate < 0);
    return firstNegative?.month ?? null;
  }, [data]);

  // Calculate max rate for Y-axis (add padding)
  const maxRate = useMemo(() => {
    if (data.length === 0) return 0.1;
    const max = Math.max(...data.map((d) => d.interestRate));
    return max + 0.00125;
  }, [data]);

  // Transform data: clip negative rates to zero for display
  const chartData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      displayRate: Math.max(0, d.interestRate),
    }));
  }, [data]);

  // Format rate as percentage (e.g., 0.035 -> "3.50%")
  const formatRate = (value: number) => `${(value * 100).toFixed(2)}%`;

  // Custom tooltip content
  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{ payload: EfficientFrontierData & { displayRate: number } }>;
  }) => {
    if (active && payload && payload.length > 0) {
      const point = payload[0].payload;
      return (
        <div className="bg-white border border-gray-200 rounded shadow-lg p-3">
          <p className="font-medium">Month {point.month}</p>
          <p className="text-gray-600">
            Break-even rate: {formatRate(point.interestRate)}
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
      aria-label="Efficient Frontier Chart showing break-even interest rates by month"
    >
      <h3 className="text-center font-semibold text-gray-800 mb-4">
        Line of Total Interest Break Even
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <XAxis
            dataKey="month"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickLine={false}
          >
            <Label
              value="Month Since Original Origination"
              position="bottom"
              offset={20}
              style={{ fill: '#374151', fontSize: 12 }}
            />
          </XAxis>
          <YAxis
            domain={[0, maxRate]}
            tickFormatter={formatRate}
            tickLine={false}
          >
            <Label
              value="Refinance Interest Rate"
              angle={-90}
              position="insideLeft"
              style={{ textAnchor: 'middle', fill: '#374151', fontSize: 12 }}
            />
          </YAxis>
          <Tooltip content={<CustomTooltip />} />

          {/* Green filled area - the efficient frontier */}
          <Area
            type="monotone"
            dataKey="displayRate"
            stroke="#22c55e"
            fill="#22c55e"
            fillOpacity={0.6}
            name="Break-even Rate"
          />

          {/* Red vertical line at break-even boundary (where rates go negative) */}
          {negativeMonth !== null && (
            <ReferenceLine
              x={negativeMonth}
              stroke="#ef4444"
              strokeWidth={2}
              label={{
                value: 'No Refinance Benefit',
                position: 'top',
                fill: '#ef4444',
                fontSize: 10,
              }}
            />
          )}

          {/* Current target position marker */}
          <ReferenceDot
            x={currentMonth}
            y={targetRate}
            r={8}
            fill="#3b82f6"
            stroke="#1d4ed8"
            strokeWidth={2}
          />

          {/* "Pay Less in Interest" label - positioned in the green zone */}
          <ReferenceDot
            x={Math.min(25, data.length > 0 ? data[Math.floor(data.length * 0.1)]?.month ?? 25 : 25)}
            y={0.005}
            r={0}
            label={{
              value: 'Pay Less in Interest',
              position: 'right',
              fill: '#166534',
              fontSize: 11,
              fontWeight: 'bold',
            }}
          />

          {/* "Pay More in Interest" label - positioned above the frontier */}
          <ReferenceDot
            x={negativeMonth ? negativeMonth * 0.8 : (data.length > 0 ? data[Math.floor(data.length * 0.7)]?.month ?? 100 : 100)}
            y={maxRate - 0.005}
            r={0}
            label={{
              value: 'Pay More in Interest',
              position: 'left',
              fill: '#991b1b',
              fontSize: 11,
              fontWeight: 'bold',
            }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Current Target legend */}
      <div className="flex justify-center items-center mt-2 text-sm text-gray-600">
        <span
          className="inline-block w-3 h-3 rounded-full mr-2"
          style={{ backgroundColor: '#3b82f6' }}
        />
        <span>Current Target (Month {currentMonth}, Rate {formatRate(targetRate)})</span>
      </div>
    </div>
  );
}
