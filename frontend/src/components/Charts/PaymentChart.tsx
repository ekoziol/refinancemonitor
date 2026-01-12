import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { Data, Layout, Config, Shape } from 'plotly.js';

export interface PaymentChartData {
  rate: number;
  monthlyPayment: number;
}

export interface PaymentChartProps {
  originalPrincipalData: PaymentChartData[];
  remainingPrincipalData: PaymentChartData[];
  currentRate: number;
  currentPayment: number;
  targetRate: number;
  targetPayment: number;
}

/**
 * Payment Chart
 *
 * Visualizes monthly payment vs interest rate for both original and remaining principal.
 * Shows reference lines for current and target rate/payment values.
 */
export function PaymentChart({
  originalPrincipalData,
  remainingPrincipalData,
  currentRate,
  currentPayment,
  targetRate,
  targetPayment,
}: PaymentChartProps) {
  // Calculate Y-axis range for proper shape positioning
  const yAxisRange = useMemo(() => {
    const allPayments = [
      ...originalPrincipalData.map((d) => d.monthlyPayment),
      ...remainingPrincipalData.map((d) => d.monthlyPayment),
      currentPayment,
      targetPayment,
    ].filter((p) => p !== undefined && !isNaN(p));

    if (allPayments.length === 0) return { min: 0, max: 1000 };

    const min = Math.min(...allPayments);
    const max = Math.max(...allPayments);
    const padding = (max - min) * 0.1;

    return { min: min - padding, max: max + padding };
  }, [originalPrincipalData, remainingPrincipalData, currentPayment, targetPayment]);

  // Build trace data for Plotly
  const data: Data[] = useMemo(() => {
    return [
      {
        x: originalPrincipalData.map((d) => d.rate),
        y: originalPrincipalData.map((d) => d.monthlyPayment),
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Original Principal',
        line: { color: '#3b82f6' }, // Blue
        showlegend: true,
      },
      {
        x: remainingPrincipalData.map((d) => d.rate),
        y: remainingPrincipalData.map((d) => d.monthlyPayment),
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Remaining Principal',
        line: { color: '#ef4444' }, // Red
        showlegend: true,
      },
    ];
  }, [originalPrincipalData, remainingPrincipalData]);

  // Build reference line shapes
  const shapes: Partial<Shape>[] = useMemo(() => {
    return [
      // Current rate - horizontal line
      {
        type: 'line' as const,
        x0: 0,
        y0: currentPayment,
        x1: currentRate,
        y1: currentPayment,
        line: { color: 'Black', dash: 'dash' as const },
        xref: 'x' as const,
        yref: 'y' as const,
      },
      // Current rate - vertical line
      {
        type: 'line' as const,
        x0: currentRate,
        y0: yAxisRange.min,
        x1: currentRate,
        y1: currentPayment,
        line: { color: 'Black', dash: 'dash' as const },
        xref: 'x' as const,
        yref: 'y' as const,
      },
      // Target rate - horizontal line
      {
        type: 'line' as const,
        x0: 0,
        y0: targetPayment,
        x1: targetRate,
        y1: targetPayment,
        line: { color: 'Green', dash: 'dash' as const },
        xref: 'x' as const,
        yref: 'y' as const,
      },
      // Target rate - vertical line
      {
        type: 'line' as const,
        x0: targetRate,
        y0: yAxisRange.min,
        x1: targetRate,
        y1: targetPayment,
        line: { color: 'Green', dash: 'dash' as const },
        xref: 'x' as const,
        yref: 'y' as const,
      },
    ];
  }, [currentRate, currentPayment, targetRate, targetPayment, yAxisRange]);

  // Build layout configuration
  const layout: Partial<Layout> = useMemo(() => {
    return {
      title: undefined, // Title is rendered separately for styling
      xaxis: {
        title: { text: 'Interest Rate' },
        tickformat: ',.2%',
      },
      yaxis: {
        title: { text: 'Monthly Payment' },
        tickformat: '$,.2f',
      },
      legend: {
        orientation: 'h' as const,
        yanchor: 'bottom' as const,
        y: -0.3,
        xanchor: 'left' as const,
        x: 0,
      },
      shapes,
      margin: { t: 20, r: 30, b: 80, l: 80 },
      autosize: true,
    };
  }, [shapes]);

  // Build config for interactive features
  const config: Partial<Config> = useMemo(() => {
    return {
      responsive: true,
      displayModeBar: true,
      scrollZoom: true,
      staticPlot: false,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d'] as const,
    };
  }, []);

  return (
    <div
      className="w-full"
      role="img"
      aria-label="Payment Chart showing monthly payment by interest rate"
      data-testid="payment-chart"
    >
      <h3 className="text-center font-semibold text-gray-800 mb-4">
        Monthly Payment by Interest Rate
      </h3>
      <Plot
        data={data}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '400px' }}
        data-testid="plotly-chart"
      />
    </div>
  );
}
