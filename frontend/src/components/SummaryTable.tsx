import type { CalculatorResponse } from '../types/calculator';

interface SummaryTableProps {
  results: CalculatorResponse | null;
  isLoading?: boolean;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

function formatPercent(value: number): string {
  return `${value.toFixed(3)}%`;
}

function formatMonths(value: number | null): string {
  if (value === null) return 'N/A';
  if (value <= 0) return 'N/A';
  const years = Math.floor(value / 12);
  const months = value % 12;
  if (years === 0) return `${months} months`;
  if (months === 0) return `${years} years`;
  return `${years}y ${months}m`;
}

interface SummaryRowProps {
  label: string;
  value: string;
  highlight?: 'positive' | 'negative' | 'neutral';
}

function SummaryRow({ label, value, highlight }: SummaryRowProps) {
  const valueClasses = {
    positive: 'text-green-600 font-semibold',
    negative: 'text-red-600 font-semibold',
    neutral: 'text-gray-900',
  };

  return (
    <tr className="border-b border-gray-100">
      <th className="py-3 pr-4 text-left text-sm font-medium text-gray-600">{label}</th>
      <td className={`py-3 text-right text-sm ${valueClasses[highlight || 'neutral']}`}>
        {value}
      </td>
    </tr>
  );
}

export function SummaryTable({ results, isLoading }: SummaryTableProps) {
  if (!results && !isLoading) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        Enter your mortgage details and click Calculate to see your refinance savings.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-lg p-6">
        <div className="animate-pulse space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex justify-between">
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!results) return null;

  const savingsPositive = results.monthlySavings > 0;
  const totalSavingsPositive = results.totalLoanSavings > 0;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Refinance Summary</h3>
      </div>

      <div className="p-4">
        <table className="w-full">
          <tbody>
            <SummaryRow
              label="Original Monthly Payment"
              value={formatCurrency(results.originalMonthlyPayment)}
            />
            <SummaryRow
              label="New Monthly Payment"
              value={formatCurrency(results.refiMonthlyPayment)}
            />
            <SummaryRow
              label="Monthly Savings"
              value={formatCurrency(results.monthlySavings)}
              highlight={savingsPositive ? 'positive' : 'negative'}
            />
            <SummaryRow
              label="Target Interest Rate"
              value={formatPercent(results.targetInterestRate)}
            />
            <SummaryRow
              label="Total Interest Savings"
              value={formatCurrency(results.totalLoanSavings)}
              highlight={totalSavingsPositive ? 'positive' : 'negative'}
            />
            <SummaryRow
              label="Break-even (Monthly Savings)"
              value={formatMonths(results.monthsToBreakevenSimple)}
            />
            <SummaryRow
              label="Break-even (Interest Savings)"
              value={formatMonths(results.monthsToBreakevenInterest)}
            />
            <SummaryRow
              label="Additional Loan Duration"
              value={formatMonths(results.additionalMonths)}
              highlight={results.additionalMonths > 0 ? 'negative' : 'positive'}
            />
            <SummaryRow
              label="Cash Required"
              value={formatCurrency(results.cashRequired)}
            />
          </tbody>
        </table>
      </div>

      {totalSavingsPositive && (
        <div className="bg-green-50 px-4 py-3 border-t border-green-100">
          <p className="text-sm text-green-800">
            <span className="font-semibold">Good news!</span> This refinance scenario saves you{' '}
            <span className="font-semibold">{formatCurrency(results.totalLoanSavings)}</span> over
            the life of the loan.
          </p>
        </div>
      )}

      {!totalSavingsPositive && results.monthlySavings > 0 && (
        <div className="bg-yellow-50 px-4 py-3 border-t border-yellow-100">
          <p className="text-sm text-yellow-800">
            <span className="font-semibold">Note:</span> While your monthly payment decreases,
            you'll pay more in total interest over the loan's lifetime.
          </p>
        </div>
      )}
    </div>
  );
}
