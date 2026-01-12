import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PaymentChart } from './PaymentChart';
import type { PaymentChartData, PaymentChartProps } from './PaymentChart';

// Mock Plotly since it requires browser APIs not available in jsdom
vi.mock('react-plotly.js', () => ({
  default: ({ data, layout, config, style, 'data-testid': testId }: {
    data: unknown[];
    layout: Record<string, unknown>;
    config: Record<string, unknown>;
    style: Record<string, unknown>;
    'data-testid'?: string;
  }) => (
    <div
      data-testid={testId || 'plotly-chart'}
      data-plot-data={JSON.stringify(data)}
      data-plot-layout={JSON.stringify(layout)}
      data-plot-config={JSON.stringify(config)}
      style={style}
    />
  ),
}));

describe('PaymentChart', () => {
  const sampleOriginalData: PaymentChartData[] = [
    { rate: 0.01, monthlyPayment: 1500 },
    { rate: 0.02, monthlyPayment: 1650 },
    { rate: 0.03, monthlyPayment: 1800 },
    { rate: 0.04, monthlyPayment: 1950 },
    { rate: 0.05, monthlyPayment: 2100 },
  ];

  const sampleRemainingData: PaymentChartData[] = [
    { rate: 0.01, monthlyPayment: 1200 },
    { rate: 0.02, monthlyPayment: 1320 },
    { rate: 0.03, monthlyPayment: 1440 },
    { rate: 0.04, monthlyPayment: 1560 },
    { rate: 0.05, monthlyPayment: 1680 },
  ];

  const defaultProps: PaymentChartProps = {
    originalPrincipalData: sampleOriginalData,
    remainingPrincipalData: sampleRemainingData,
    currentRate: 0.045,
    currentPayment: 2015.11,
    targetRate: 0.02,
    targetPayment: 1500,
  };

  describe('rendering', () => {
    it('renders without crashing', () => {
      render(<PaymentChart {...defaultProps} />);
      expect(screen.getByTestId('payment-chart')).toBeInTheDocument();
    });

    it('renders chart title', () => {
      render(<PaymentChart {...defaultProps} />);
      expect(screen.getByText(/monthly payment by interest rate/i)).toBeInTheDocument();
    });

    it('renders with the plotly container', () => {
      render(<PaymentChart {...defaultProps} />);
      expect(screen.getByTestId('plotly-chart')).toBeInTheDocument();
    });
  });

  describe('data structure', () => {
    it('passes original principal data as first trace', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      expect(plotData.length).toBeGreaterThanOrEqual(2);
      expect(plotData[0].name).toBe('Original Principal');
      expect(plotData[0].x).toEqual(sampleOriginalData.map(d => d.rate));
      expect(plotData[0].y).toEqual(sampleOriginalData.map(d => d.monthlyPayment));
    });

    it('passes remaining principal data as second trace', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      expect(plotData[1].name).toBe('Remaining Principal');
      expect(plotData[1].x).toEqual(sampleRemainingData.map(d => d.rate));
      expect(plotData[1].y).toEqual(sampleRemainingData.map(d => d.monthlyPayment));
    });

    it('uses scatter type with lines mode', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      expect(plotData[0].type).toBe('scatter');
      expect(plotData[0].mode).toBe('lines');
      expect(plotData[1].type).toBe('scatter');
      expect(plotData[1].mode).toBe('lines');
    });
  });

  describe('axes configuration', () => {
    it('configures x-axis with interest rate title', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(layout.xaxis.title.text).toBe('Interest Rate');
    });

    it('configures y-axis with monthly payment title', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(layout.yaxis.title.text).toBe('Monthly Payment');
    });

    it('formats x-axis as percentage', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(layout.xaxis.tickformat).toBe(',.2%');
    });

    it('formats y-axis as currency', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(layout.yaxis.tickformat).toBe('$,.2f');
    });
  });

  describe('series labels', () => {
    it('has correct legend labels', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      const seriesNames = plotData.map((trace: { name: string }) => trace.name);
      expect(seriesNames).toContain('Original Principal');
      expect(seriesNames).toContain('Remaining Principal');
    });

    it('includes original principal in legend', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      const originalTrace = plotData.find((t: { name: string }) => t.name === 'Original Principal');
      expect(originalTrace.showlegend).not.toBe(false);
    });

    it('includes remaining principal in legend', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      const remainingTrace = plotData.find((t: { name: string }) => t.name === 'Remaining Principal');
      expect(remainingTrace.showlegend).not.toBe(false);
    });
  });

  describe('reference lines', () => {
    it('includes reference shapes for current rate and payment', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(layout.shapes).toBeDefined();
      expect(layout.shapes.length).toBeGreaterThanOrEqual(2);
    });

    it('includes horizontal line for current payment', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      const horizontalCurrentLine = layout.shapes.find(
        (s: { y0: number; y1: number; line: { color: string } }) =>
          s.y0 === defaultProps.currentPayment &&
          s.y1 === defaultProps.currentPayment
      );
      expect(horizontalCurrentLine).toBeDefined();
    });

    it('includes vertical line for current rate', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      const verticalCurrentLine = layout.shapes.find(
        (s: { x0: number; x1: number }) =>
          s.x0 === defaultProps.currentRate &&
          s.x1 === defaultProps.currentRate
      );
      expect(verticalCurrentLine).toBeDefined();
    });

    it('includes reference lines for target rate and payment', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      const horizontalTargetLine = layout.shapes.find(
        (s: { y0: number; y1: number; line: { color: string } }) =>
          s.y0 === defaultProps.targetPayment &&
          s.y1 === defaultProps.targetPayment &&
          s.line.color === 'Green'
      );
      expect(horizontalTargetLine).toBeDefined();
    });
  });

  describe('interactive features', () => {
    it('enables hover interaction', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const config = JSON.parse(plotElement.getAttribute('data-plot-config') || '{}');

      // Plotly has hover enabled by default, just verify it's not disabled
      expect(config.staticPlot).not.toBe(true);
    });

    it('enables zoom interaction', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const config = JSON.parse(plotElement.getAttribute('data-plot-config') || '{}');

      expect(config.scrollZoom).toBe(true);
    });

    it('enables pan interaction via modebar', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const config = JSON.parse(plotElement.getAttribute('data-plot-config') || '{}');

      expect(config.displayModeBar).toBe(true);
    });

    it('enables responsive sizing', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const config = JSON.parse(plotElement.getAttribute('data-plot-config') || '{}');

      expect(config.responsive).toBe(true);
    });
  });

  describe('legend configuration', () => {
    it('positions legend at bottom', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      expect(layout.legend.orientation).toBe('h');
      expect(layout.legend.yanchor).toBe('bottom');
    });
  });

  describe('empty data handling', () => {
    it('renders gracefully with empty original data', () => {
      render(<PaymentChart {...defaultProps} originalPrincipalData={[]} />);
      expect(screen.getByTestId('payment-chart')).toBeInTheDocument();
    });

    it('renders gracefully with empty remaining data', () => {
      render(<PaymentChart {...defaultProps} remainingPrincipalData={[]} />);
      expect(screen.getByTestId('payment-chart')).toBeInTheDocument();
    });

    it('renders gracefully with both empty datasets', () => {
      render(
        <PaymentChart
          {...defaultProps}
          originalPrincipalData={[]}
          remainingPrincipalData={[]}
        />
      );
      expect(screen.getByTestId('payment-chart')).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('has accessible name for screen readers', () => {
      render(<PaymentChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /payment chart/i })).toBeInTheDocument();
    });

    it('has descriptive aria-label', () => {
      render(<PaymentChart {...defaultProps} />);
      const chart = screen.getByRole('img');
      expect(chart).toHaveAttribute('aria-label', expect.stringContaining('monthly payment'));
    });
  });

  describe('props validation', () => {
    it('accepts required props without errors', () => {
      expect(() => {
        render(<PaymentChart {...defaultProps} />);
      }).not.toThrow();
    });

    it('updates when props change', () => {
      const { rerender } = render(<PaymentChart {...defaultProps} />);

      const newRate = 0.03;
      rerender(<PaymentChart {...defaultProps} currentRate={newRate} />);
      const plotElement = screen.getByTestId('plotly-chart');

      const updatedLayout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');
      const verticalLine = updatedLayout.shapes.find(
        (s: { x0: number; x1: number; line: { dash: string } }) =>
          s.x0 === newRate && s.x1 === newRate && s.line.dash === 'dash'
      );
      expect(verticalLine).toBeDefined();
    });
  });

  describe('styling', () => {
    it('uses appropriate colors for traces', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const plotData = JSON.parse(plotElement.getAttribute('data-plot-data') || '[]');

      // Original Principal should be blue
      expect(plotData[0].line.color).toBeDefined();
      // Remaining Principal should be a different color (red/orange)
      expect(plotData[1].line.color).toBeDefined();
      expect(plotData[0].line.color).not.toBe(plotData[1].line.color);
    });

    it('uses dashed lines for reference markers', () => {
      render(<PaymentChart {...defaultProps} />);
      const plotElement = screen.getByTestId('plotly-chart');
      const layout = JSON.parse(plotElement.getAttribute('data-plot-layout') || '{}');

      const dashedLines = layout.shapes.filter(
        (s: { line: { dash: string } }) => s.line.dash === 'dash'
      );
      expect(dashedLines.length).toBeGreaterThan(0);
    });
  });

  describe('snapshot', () => {
    it('matches snapshot for default props', () => {
      const { container } = render(<PaymentChart {...defaultProps} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with different data', () => {
      const newData: PaymentChartData[] = [
        { rate: 0.02, monthlyPayment: 1800 },
        { rate: 0.04, monthlyPayment: 2200 },
      ];
      const { container } = render(
        <PaymentChart
          {...defaultProps}
          originalPrincipalData={newData}
          remainingPrincipalData={newData}
          currentRate={0.03}
          currentPayment={2000}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
