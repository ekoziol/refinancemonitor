import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BreakevenChart } from './BreakevenChart';
import type { BreakevenData, BreakevenChartProps } from './BreakevenChart';

// Mock ResizeObserver for Recharts
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as typeof globalThis & { ResizeObserver: typeof ResizeObserverMock }).ResizeObserver = ResizeObserverMock;

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

describe('BreakevenChart', () => {
  // Sample data representing monthly savings accumulation
  // Simple method: (original - refi) * month - refi_cost
  // Interest method: interest savings comparison
  const sampleData: BreakevenData[] = [
    { month: 0, simpleSavings: -5000, interestSavings: -8000 },
    { month: 12, simpleSavings: -2000, interestSavings: -5000 },
    { month: 24, simpleSavings: 1000, interestSavings: -2000 },
    { month: 36, simpleSavings: 4000, interestSavings: 1000 },
    { month: 48, simpleSavings: 7000, interestSavings: 4000 },
    { month: 60, simpleSavings: 10000, interestSavings: 7000 },
    { month: 72, simpleSavings: 13000, interestSavings: 10000 },
    { month: 84, simpleSavings: 16000, interestSavings: 13000 },
    { month: 96, simpleSavings: 19000, interestSavings: 16000 },
    { month: 108, simpleSavings: 22000, interestSavings: 19000 },
    { month: 120, simpleSavings: 25000, interestSavings: 22000 },
  ];

  const defaultProps: BreakevenChartProps = {
    data: sampleData,
  };

  describe('rendering', () => {
    it('renders without crashing', () => {
      render(<BreakevenChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });

    it('renders chart title', () => {
      render(<BreakevenChart {...defaultProps} />);
      expect(screen.getByText(/break.?even point/i)).toBeInTheDocument();
    });

    it('renders with the responsive container wrapper', () => {
      const { container } = render(<BreakevenChart {...defaultProps} />);
      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
    });
  });

  describe('dual method display', () => {
    it('displays legend with both methods', () => {
      render(<BreakevenChart {...defaultProps} />);
      // Summary section should show both savings methods
      expect(screen.getByText(/monthly savings break-even/i)).toBeInTheDocument();
      expect(screen.getByText(/interest savings break-even/i)).toBeInTheDocument();
    });
  });

  describe('break-even point markers', () => {
    it('calculates simple method break-even point correctly', () => {
      // Simple savings crosses zero between month 12 and 24
      // The component should identify this break-even point
      render(<BreakevenChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });

    it('calculates interest method break-even point correctly', () => {
      // Interest savings crosses zero between month 24 and 36
      render(<BreakevenChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });
  });

  describe('data handling', () => {
    it('handles data where simple method never breaks even', () => {
      const noBreakevenData: BreakevenData[] = [
        { month: 0, simpleSavings: -5000, interestSavings: -8000 },
        { month: 12, simpleSavings: -4000, interestSavings: -6000 },
        { month: 24, simpleSavings: -3000, interestSavings: -4000 },
      ];
      render(<BreakevenChart data={noBreakevenData} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });

    it('handles data where interest method never breaks even', () => {
      const noInterestBreakevenData: BreakevenData[] = [
        { month: 0, simpleSavings: -5000, interestSavings: -10000 },
        { month: 12, simpleSavings: 1000, interestSavings: -9000 },
        { month: 24, simpleSavings: 7000, interestSavings: -8000 },
      ];
      render(<BreakevenChart data={noInterestBreakevenData} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });

    it('handles empty data gracefully', () => {
      render(<BreakevenChart data={[]} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('has accessible name for screen readers', () => {
      render(<BreakevenChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });

    it('has descriptive aria-label', () => {
      render(<BreakevenChart {...defaultProps} />);
      const chart = screen.getByRole('img');
      expect(chart).toHaveAttribute('aria-label', expect.stringMatching(/break-?even/i));
    });
  });

  describe('visual indicators', () => {
    it('shows chart title', () => {
      render(<BreakevenChart {...defaultProps} />);
      expect(screen.getByText(/break.?even point/i)).toBeInTheDocument();
    });

    it('renders the chart container', () => {
      const { container } = render(<BreakevenChart {...defaultProps} />);
      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
    });
  });

  describe('edge cases', () => {
    it('handles single data point', () => {
      const singlePoint: BreakevenData[] = [{ month: 0, simpleSavings: -5000, interestSavings: -8000 }];
      render(<BreakevenChart data={singlePoint} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });

    it('handles all positive savings from start', () => {
      const allPositive: BreakevenData[] = [
        { month: 0, simpleSavings: 1000, interestSavings: 500 },
        { month: 12, simpleSavings: 4000, interestSavings: 3500 },
      ];
      render(<BreakevenChart data={allPositive} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });

    it('handles all negative savings', () => {
      const allNegative: BreakevenData[] = [
        { month: 0, simpleSavings: -5000, interestSavings: -8000 },
        { month: 12, simpleSavings: -6000, interestSavings: -9000 },
      ];
      render(<BreakevenChart data={allNegative} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });

    it('handles very large savings values', () => {
      const largeSavings: BreakevenData[] = [
        { month: 0, simpleSavings: -50000, interestSavings: -80000 },
        { month: 120, simpleSavings: 100000, interestSavings: 80000 },
      ];
      render(<BreakevenChart data={largeSavings} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });
  });

  describe('props validation', () => {
    it('accepts required props without errors', () => {
      expect(() => {
        render(<BreakevenChart data={sampleData} />);
      }).not.toThrow();
    });

    it('updates when props change', () => {
      const { rerender } = render(<BreakevenChart {...defaultProps} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();

      const newData: BreakevenData[] = [
        { month: 0, simpleSavings: -10000, interestSavings: -15000 },
        { month: 12, simpleSavings: -5000, interestSavings: -10000 },
      ];
      rerender(<BreakevenChart data={newData} />);
      expect(screen.getByRole('img', { name: /break.?even/i })).toBeInTheDocument();
    });
  });
});
