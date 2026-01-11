import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SummaryTable } from './SummaryTable';
import type { CalculatorResponse } from '../types/calculator';

const mockResults: CalculatorResponse = {
  originalMonthlyPayment: 2026.74,
  minimumMonthlyPayment: 1111.11,
  refiMonthlyPayment: 1798.65,
  monthlySavings: 228.09,
  targetInterestRate: 5.5,
  originalInterest: 329227.44,
  refiInterest: 247513.58,
  totalLoanSavings: 76713.86,
  monthsToBreakevenSimple: 22,
  monthsToBreakevenInterest: 36,
  additionalMonths: 60,
  cashRequired: 5000,
};

describe('SummaryTable', () => {
  describe('empty state', () => {
    it('shows placeholder when no results and not loading', () => {
      render(<SummaryTable results={null} />);

      expect(
        screen.getByText(/Enter your mortgage details/i)
      ).toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('shows skeleton loader when loading without results', () => {
      render(<SummaryTable results={null} isLoading={true} />);

      // Should show skeleton animation
      const skeleton = document.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });
  });

  describe('with results', () => {
    it('displays all summary fields', () => {
      render(<SummaryTable results={mockResults} />);

      expect(screen.getByText('Refinance Summary')).toBeInTheDocument();
      expect(screen.getByText('Original Monthly Payment')).toBeInTheDocument();
      expect(screen.getByText('New Monthly Payment')).toBeInTheDocument();
      expect(screen.getByText('Monthly Savings')).toBeInTheDocument();
      expect(screen.getByText('Target Interest Rate')).toBeInTheDocument();
      expect(screen.getByText('Total Interest Savings')).toBeInTheDocument();
      expect(screen.getByText('Break-even (Monthly Savings)')).toBeInTheDocument();
      expect(screen.getByText('Break-even (Interest Savings)')).toBeInTheDocument();
      expect(screen.getByText('Additional Loan Duration')).toBeInTheDocument();
      expect(screen.getByText('Cash Required')).toBeInTheDocument();
    });

    it('formats currency values correctly', () => {
      render(<SummaryTable results={mockResults} />);

      expect(screen.getByText('$2,026.74')).toBeInTheDocument(); // Original payment
      expect(screen.getByText('$1,798.65')).toBeInTheDocument(); // Refi payment
      expect(screen.getByText('$228.09')).toBeInTheDocument(); // Monthly savings
      expect(screen.getByText('$5,000.00')).toBeInTheDocument(); // Cash required
    });

    it('formats percentage correctly', () => {
      render(<SummaryTable results={mockResults} />);

      expect(screen.getByText('5.500%')).toBeInTheDocument();
    });

    it('formats break-even months correctly', () => {
      render(<SummaryTable results={mockResults} />);

      expect(screen.getByText('1y 10m')).toBeInTheDocument(); // 22 months
      expect(screen.getByText('3 years')).toBeInTheDocument(); // 36 months
    });

    it('shows positive message when total savings is positive', () => {
      render(<SummaryTable results={mockResults} />);

      expect(screen.getByText(/Good news!/i)).toBeInTheDocument();
      // Value appears twice - in table and in message
      const savingsElements = screen.getAllByText(/\$76,713\.86/);
      expect(savingsElements.length).toBe(2);
    });

    it('shows warning when monthly savings positive but total savings negative', () => {
      const resultsWithNegativeSavings = {
        ...mockResults,
        totalLoanSavings: -5000,
        monthlySavings: 100,
      };

      render(<SummaryTable results={resultsWithNegativeSavings} />);

      expect(screen.getByText(/Note:/i)).toBeInTheDocument();
      expect(screen.getByText(/pay more in total interest/i)).toBeInTheDocument();
    });

    it('handles null break-even values', () => {
      const resultsWithNullBreakeven = {
        ...mockResults,
        monthsToBreakevenSimple: null,
        monthsToBreakevenInterest: null,
      };

      render(<SummaryTable results={resultsWithNullBreakeven} />);

      // Should show N/A for null values
      const naElements = screen.getAllByText('N/A');
      expect(naElements.length).toBeGreaterThanOrEqual(2);
    });

    it('highlights positive savings in green', () => {
      render(<SummaryTable results={mockResults} />);

      const savingsCell = screen.getByText('$228.09');
      expect(savingsCell).toHaveClass('text-green-600');
    });

    it('highlights negative additional months in red', () => {
      render(<SummaryTable results={mockResults} />);

      const additionalMonthsCell = screen.getByText('5 years'); // 60 months
      expect(additionalMonthsCell).toHaveClass('text-red-600');
    });
  });
});
