import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SummaryTable, type SummaryData } from './SummaryTable';

describe('SummaryTable', () => {
  const defaultData: SummaryData = {
    originalMonthlyPayment: 1500.00,
    refiMonthlyPayment: 1200.00,
    originalTotalInterest: 180000.00,
    refiTotalInterest: 150000.00,
    breakEvenMonths: 24,
    breakEvenInterestOnlyMonths: 36,
    originalRemainingTerm: 300, // 25 years
    refiTerm: 360, // 30 years
    refinanceCost: 5000.00,
  };

  it('renders the summary table with heading', () => {
    render(<SummaryTable data={defaultData} />);
    expect(screen.getByRole('heading', { name: /refinance summary/i })).toBeInTheDocument();
  });

  describe('Monthly Payment Section', () => {
    it('displays original monthly payment with currency formatting', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Original Payment')).toBeInTheDocument();
      expect(screen.getByText('$1,500.00')).toBeInTheDocument();
    });

    it('displays refinance monthly payment with currency formatting', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Refinance Payment')).toBeInTheDocument();
      expect(screen.getByText('$1,200.00')).toBeInTheDocument();
    });

    it('displays monthly savings with currency formatting', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Monthly Savings')).toBeInTheDocument();
      expect(screen.getByText('$300.00')).toBeInTheDocument();
    });

    it('highlights positive monthly savings in green', () => {
      render(<SummaryTable data={defaultData} />);
      const savingsValue = screen.getByText('$300.00');
      expect(savingsValue).toHaveClass('text-green-600');
    });

    it('highlights negative monthly savings in red', () => {
      const dataWithHigherRefi: SummaryData = {
        ...defaultData,
        refiMonthlyPayment: 1600.00,
      };
      render(<SummaryTable data={dataWithHigherRefi} />);
      // Negative savings: 1500 - 1600 = -100
      expect(screen.getByText('-$100.00')).toHaveClass('text-red-600');
    });
  });

  describe('Total Interest Section', () => {
    it('displays original total interest with currency formatting', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Original Total Interest')).toBeInTheDocument();
      expect(screen.getByText('$180,000.00')).toBeInTheDocument();
    });

    it('displays refinance total interest with currency formatting', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Refinance Total Interest')).toBeInTheDocument();
      expect(screen.getByText('$150,000.00')).toBeInTheDocument();
    });

    it('displays interest savings with currency formatting', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Interest Savings')).toBeInTheDocument();
      expect(screen.getByText('$30,000.00')).toBeInTheDocument();
    });

    it('highlights positive interest savings in green', () => {
      render(<SummaryTable data={defaultData} />);
      const savingsValue = screen.getByText('$30,000.00');
      expect(savingsValue).toHaveClass('text-green-600');
    });

    it('highlights negative interest savings in red', () => {
      const dataWithHigherRefiInterest: SummaryData = {
        ...defaultData,
        refiTotalInterest: 200000.00,
      };
      render(<SummaryTable data={dataWithHigherRefiInterest} />);
      // Interest savings would be negative
      expect(screen.getByText('-$20,000.00')).toHaveClass('text-red-600');
    });
  });

  describe('Break-Even Section', () => {
    it('displays simple break-even time in months', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Simple Break-Even')).toBeInTheDocument();
      expect(screen.getByText('2 years')).toBeInTheDocument();
    });

    it('displays interest-only break-even time when provided', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Interest-Only Break-Even')).toBeInTheDocument();
      expect(screen.getByText('3 years')).toBeInTheDocument();
    });

    it('does not display interest-only break-even when null', () => {
      const dataWithoutInterestBreakEven: SummaryData = {
        ...defaultData,
        breakEvenInterestOnlyMonths: null,
      };
      render(<SummaryTable data={dataWithoutInterestBreakEven} />);
      expect(screen.queryByText('Interest-Only Break-Even')).not.toBeInTheDocument();
    });

    it('displays refinance cost with currency formatting', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Refinance Cost')).toBeInTheDocument();
      expect(screen.getByText('$5,000.00')).toBeInTheDocument();
    });

    it('formats months correctly for various durations', () => {
      // Test with 1 month (disable interest-only to avoid duplicate matches)
      const oneMonthData: SummaryData = {
        ...defaultData,
        breakEvenMonths: 1,
        breakEvenInterestOnlyMonths: null,
      };
      const { rerender } = render(<SummaryTable data={oneMonthData} />);
      expect(screen.getByText('1 month')).toBeInTheDocument();

      // Test with 6 months
      rerender(<SummaryTable data={{ ...defaultData, breakEvenMonths: 6, breakEvenInterestOnlyMonths: null }} />);
      expect(screen.getByText('6 months')).toBeInTheDocument();

      // Test with 18 months (1 year, 6 months)
      rerender(<SummaryTable data={{ ...defaultData, breakEvenMonths: 18, breakEvenInterestOnlyMonths: null }} />);
      expect(screen.getByText('1 year, 6 months')).toBeInTheDocument();

      // Test with 48 months (4 years) - using different value to avoid matching loan terms
      rerender(<SummaryTable data={{ ...defaultData, breakEvenMonths: 48, breakEvenInterestOnlyMonths: null }} />);
      expect(screen.getByText('4 years')).toBeInTheDocument();
    });
  });

  describe('Loan Term Section', () => {
    it('displays original remaining term', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Original Remaining Term')).toBeInTheDocument();
      expect(screen.getByText('25 years')).toBeInTheDocument();
    });

    it('displays new loan term', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('New Loan Term')).toBeInTheDocument();
      expect(screen.getByText('30 years')).toBeInTheDocument();
    });

    it('displays term extension when loan is extended', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByText('Term Extension')).toBeInTheDocument();
      // 360 - 300 = 60 months = 5 years
      expect(screen.getByText('+5 years')).toBeInTheDocument();
    });

    it('highlights term extension in red (negative impact)', () => {
      render(<SummaryTable data={defaultData} />);
      const extensionValue = screen.getByText('+5 years');
      expect(extensionValue).toHaveClass('text-red-600');
    });

    it('displays term reduction in green', () => {
      const dataWithShorterTerm: SummaryData = {
        ...defaultData,
        refiTerm: 240, // 20 years, shorter than 25 years remaining
      };
      render(<SummaryTable data={dataWithShorterTerm} />);
      // 240 - 300 = -60 months = 5 years reduction
      expect(screen.getByText('-5 years')).toHaveClass('text-green-600');
    });

    it('displays no change when terms are equal', () => {
      const dataWithSameTerm: SummaryData = {
        ...defaultData,
        refiTerm: 300,
      };
      render(<SummaryTable data={dataWithSameTerm} />);
      expect(screen.getByText('No change')).toBeInTheDocument();
    });
  });

  describe('Recommendation Banner', () => {
    it('shows positive recommendation when refinance is beneficial', () => {
      render(<SummaryTable data={defaultData} />);
      // Interest savings ($30,000) > refinance cost ($5,000)
      expect(screen.getByRole('alert')).toHaveTextContent(/save you money/i);
    });

    it('shows negative recommendation when refinance is not beneficial', () => {
      const dataNotBeneficial: SummaryData = {
        ...defaultData,
        originalTotalInterest: 150000,
        refiTotalInterest: 148000, // Only $2,000 savings, less than $5,000 cost
      };
      render(<SummaryTable data={dataNotBeneficial} />);
      expect(screen.getByRole('alert')).toHaveTextContent(/may not be beneficial/i);
    });

    it('has green background for beneficial refinance', () => {
      render(<SummaryTable data={defaultData} />);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('bg-green-50');
    });

    it('has red background for non-beneficial refinance', () => {
      const dataNotBeneficial: SummaryData = {
        ...defaultData,
        originalTotalInterest: 150000,
        refiTotalInterest: 148000,
      };
      render(<SummaryTable data={dataNotBeneficial} />);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('bg-red-50');
    });
  });

  describe('Currency Formatting', () => {
    it('formats large numbers with commas', () => {
      const largeData: SummaryData = {
        ...defaultData,
        originalTotalInterest: 1234567.89,
      };
      render(<SummaryTable data={largeData} />);
      expect(screen.getByText('$1,234,567.89')).toBeInTheDocument();
    });

    it('formats numbers with two decimal places', () => {
      const preciseData: SummaryData = {
        ...defaultData,
        originalMonthlyPayment: 1234.5,
      };
      render(<SummaryTable data={preciseData} />);
      expect(screen.getByText('$1,234.50')).toBeInTheDocument();
    });

    it('handles zero values', () => {
      const zeroData: SummaryData = {
        ...defaultData,
        refinanceCost: 0,
      };
      render(<SummaryTable data={zeroData} />);
      expect(screen.getByText('$0.00')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses proper heading hierarchy', () => {
      render(<SummaryTable data={defaultData} />);
      const mainHeading = screen.getByRole('heading', { level: 2 });
      expect(mainHeading).toHaveTextContent('Refinance Summary');

      const sectionHeadings = screen.getAllByRole('heading', { level: 3 });
      expect(sectionHeadings).toHaveLength(4);
    });

    it('uses definition list for data presentation', () => {
      const { container } = render(<SummaryTable data={defaultData} />);
      expect(container.querySelector('dl')).toBeInTheDocument();
    });

    it('has alert role for recommendation banner', () => {
      render(<SummaryTable data={defaultData} />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('has responsive container classes', () => {
      const { container } = render(<SummaryTable data={defaultData} />);
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass('p-4', 'sm:p-6');
    });

    it('has responsive flex direction classes on rows', () => {
      const { container } = render(<SummaryTable data={defaultData} />);
      const rows = container.querySelectorAll('.flex.flex-col.sm\\:flex-row');
      expect(rows.length).toBeGreaterThan(0);
    });
  });
});
