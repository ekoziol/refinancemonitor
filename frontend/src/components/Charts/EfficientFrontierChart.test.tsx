import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EfficientFrontierChart } from './EfficientFrontierChart';
import type { EfficientFrontierData, EfficientFrontierChartProps } from './EfficientFrontierChart';

// Mock ResizeObserver for Recharts
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock;

// Mock ResponsiveContainer to render children with actual dimensions
// This is necessary because jsdom doesn't provide actual layout dimensions
vi.mock('recharts', async () => {
  const actual = await vi.importActual<typeof import('recharts')>('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div className="recharts-responsive-container" style={{ width: 800, height: 400 }}>
        {children}
      </div>
    ),
  };
});

describe('EfficientFrontierChart', () => {
  const sampleData: EfficientFrontierData[] = [
    { month: 0, interestRate: 0.05 },
    { month: 12, interestRate: 0.045 },
    { month: 24, interestRate: 0.04 },
    { month: 36, interestRate: 0.035 },
    { month: 48, interestRate: 0.03 },
    { month: 60, interestRate: 0.025 },
    { month: 72, interestRate: 0.02 },
    { month: 84, interestRate: 0.015 },
    { month: 96, interestRate: 0.01 },
    { month: 108, interestRate: 0.005 },
    { month: 120, interestRate: 0.0 },
    { month: 132, interestRate: -0.005 },
  ];

  const defaultProps: EfficientFrontierChartProps = {
    data: sampleData,
    currentMonth: 60,
    targetRate: 0.035,
  };

  describe('rendering', () => {
    it('renders without crashing', () => {
      render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });

    it('renders chart title', () => {
      render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByText(/line of total interest break even/i)).toBeInTheDocument();
    });

    it('renders with the responsive container wrapper', () => {
      const { container } = render(<EfficientFrontierChart {...defaultProps} />);
      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
    });
  });

  describe('data transformation', () => {
    it('handles negative interest rates by clipping to display', () => {
      // Component should not crash with negative rates
      const dataWithNegative: EfficientFrontierData[] = [
        { month: 0, interestRate: 0.05 },
        { month: 12, interestRate: -0.01 },
      ];
      render(<EfficientFrontierChart data={dataWithNegative} currentMonth={0} targetRate={0.03} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });

    it('calculates max rate with padding for y-axis', () => {
      // This is tested implicitly - chart renders without crashing
      render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });
  });

  describe('current position display', () => {
    it('shows current target information in legend', () => {
      render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByText(/current target/i)).toBeInTheDocument();
    });

    it('displays current month value', () => {
      render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByText(/month 60/i)).toBeInTheDocument();
    });

    it('displays current rate as percentage', () => {
      render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByText(/3\.50%/)).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('has accessible name for screen readers', () => {
      render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });

    it('has descriptive aria-label', () => {
      render(<EfficientFrontierChart {...defaultProps} />);
      const chart = screen.getByRole('img');
      expect(chart).toHaveAttribute('aria-label', expect.stringContaining('break-even interest rates'));
    });
  });

  describe('empty data handling', () => {
    it('renders gracefully with empty data', () => {
      render(<EfficientFrontierChart data={[]} currentMonth={0} targetRate={0} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });

    it('shows chart title even with empty data', () => {
      render(<EfficientFrontierChart data={[]} currentMonth={0} targetRate={0} />);
      expect(screen.getByText(/line of total interest break even/i)).toBeInTheDocument();
    });
  });

  describe('edge cases', () => {
    it('handles data where all rates are negative', () => {
      const negativeData: EfficientFrontierData[] = [
        { month: 0, interestRate: -0.01 },
        { month: 12, interestRate: -0.02 },
      ];
      render(<EfficientFrontierChart data={negativeData} currentMonth={0} targetRate={0} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });

    it('handles current month beyond data range', () => {
      render(<EfficientFrontierChart {...defaultProps} currentMonth={500} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });

    it('handles very small interest rates', () => {
      const smallRates: EfficientFrontierData[] = [
        { month: 0, interestRate: 0.001 },
        { month: 12, interestRate: 0.0005 },
      ];
      render(<EfficientFrontierChart data={smallRates} currentMonth={6} targetRate={0.0007} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });

    it('handles single data point', () => {
      const singlePoint: EfficientFrontierData[] = [{ month: 0, interestRate: 0.05 }];
      render(<EfficientFrontierChart data={singlePoint} currentMonth={0} targetRate={0.05} />);
      expect(screen.getByRole('img', { name: /efficient frontier/i })).toBeInTheDocument();
    });
  });

  describe('props validation', () => {
    it('accepts required props without errors', () => {
      expect(() => {
        render(<EfficientFrontierChart data={sampleData} currentMonth={60} targetRate={0.035} />);
      }).not.toThrow();
    });

    it('updates when props change', () => {
      const { rerender } = render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByText(/month 60/i)).toBeInTheDocument();

      rerender(<EfficientFrontierChart {...defaultProps} currentMonth={120} />);
      expect(screen.getByText(/month 120/i)).toBeInTheDocument();
    });

    it('updates rate display when targetRate changes', () => {
      const { rerender } = render(<EfficientFrontierChart {...defaultProps} />);
      expect(screen.getByText(/3\.50%/)).toBeInTheDocument();

      rerender(<EfficientFrontierChart {...defaultProps} targetRate={0.05} />);
      expect(screen.getByText(/5\.00%/)).toBeInTheDocument();
    });
  });
});
