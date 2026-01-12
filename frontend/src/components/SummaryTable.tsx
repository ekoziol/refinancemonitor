export interface SummaryData {
  originalMonthlyPayment: number;
  refiMonthlyPayment: number;
  originalTotalInterest: number;
  refiTotalInterest: number;
  breakEvenMonths: number;
  breakEvenInterestOnlyMonths: number | null;
  originalRemainingTerm: number; // months
  refiTerm: number; // months
  refinanceCost: number;
}

export interface SummaryTableProps {
  data: SummaryData;
}

/**
 * Format a number as currency ($X,XXX.XX)
 */
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format months as years and months
 */
function formatMonths(months: number): string {
  const years = Math.floor(months / 12);
  const remainingMonths = months % 12;
  if (years === 0) {
    return `${remainingMonths} month${remainingMonths !== 1 ? 's' : ''}`;
  }
  if (remainingMonths === 0) {
    return `${years} year${years !== 1 ? 's' : ''}`;
  }
  return `${years} year${years !== 1 ? 's' : ''}, ${remainingMonths} month${remainingMonths !== 1 ? 's' : ''}`;
}

interface SummaryRowProps {
  label: string;
  value: string;
  highlight?: 'positive' | 'negative' | 'neutral';
  subtext?: string;
}

function SummaryRow({ label, value, highlight = 'neutral', subtext }: SummaryRowProps) {
  const valueClasses = {
    positive: 'text-green-600 font-semibold',
    negative: 'text-red-600 font-semibold',
    neutral: 'text-gray-900',
  };

  return (
    <div className="flex flex-col sm:flex-row sm:justify-between py-3 border-b border-gray-200 last:border-b-0">
      <dt className="text-sm font-medium text-gray-600">{label}</dt>
      <dd className={`text-sm mt-1 sm:mt-0 ${valueClasses[highlight]}`}>
        {value}
        {subtext && <span className="block text-xs text-gray-500 font-normal">{subtext}</span>}
      </dd>
    </div>
  );
}

/**
 * Summary Table Component
 *
 * Displays refinance calculation results including:
 * - Original vs refinance monthly payments
 * - Monthly and total interest savings
 * - Break-even time calculations
 * - Loan term comparison
 */
export function SummaryTable({ data }: SummaryTableProps) {
  const monthlySavings = data.originalMonthlyPayment - data.refiMonthlyPayment;
  const interestSavings = data.originalTotalInterest - data.refiTotalInterest;
  const termExtension = data.refiTerm - data.originalRemainingTerm;

  // Determine if refinance is beneficial overall
  const isBeneficial = interestSavings > data.refinanceCost;

  return (
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Refinance Summary</h2>

      {/* Overall recommendation banner */}
      <div
        className={`mb-6 p-3 rounded-md ${
          isBeneficial
            ? 'bg-green-50 border border-green-200'
            : 'bg-red-50 border border-red-200'
        }`}
        role="alert"
      >
        <p
          className={`text-sm font-medium ${
            isBeneficial ? 'text-green-800' : 'text-red-800'
          }`}
        >
          {isBeneficial
            ? '✓ Refinancing could save you money over the life of the loan'
            : '✗ Refinancing may not be beneficial at current terms'}
        </p>
      </div>

      <dl className="divide-y divide-gray-200">
        {/* Monthly Payment Comparison */}
        <div className="pb-4">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Monthly Payment</h3>
          <SummaryRow
            label="Original Payment"
            value={formatCurrency(data.originalMonthlyPayment)}
          />
          <SummaryRow
            label="Refinance Payment"
            value={formatCurrency(data.refiMonthlyPayment)}
          />
          <SummaryRow
            label="Monthly Savings"
            value={formatCurrency(monthlySavings)}
            highlight={monthlySavings > 0 ? 'positive' : monthlySavings < 0 ? 'negative' : 'neutral'}
          />
        </div>

        {/* Total Interest Comparison */}
        <div className="py-4">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Total Interest</h3>
          <SummaryRow
            label="Original Total Interest"
            value={formatCurrency(data.originalTotalInterest)}
          />
          <SummaryRow
            label="Refinance Total Interest"
            value={formatCurrency(data.refiTotalInterest)}
          />
          <SummaryRow
            label="Interest Savings"
            value={formatCurrency(interestSavings)}
            highlight={interestSavings > 0 ? 'positive' : interestSavings < 0 ? 'negative' : 'neutral'}
            subtext={interestSavings > 0 ? 'Over life of loan' : undefined}
          />
        </div>

        {/* Break-Even Analysis */}
        <div className="py-4">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Break-Even Time</h3>
          <SummaryRow
            label="Simple Break-Even"
            value={formatMonths(data.breakEvenMonths)}
            subtext="Based on monthly payment savings"
          />
          {data.breakEvenInterestOnlyMonths !== null && (
            <SummaryRow
              label="Interest-Only Break-Even"
              value={formatMonths(data.breakEvenInterestOnlyMonths)}
              subtext="Accounting for total interest savings"
            />
          )}
          <SummaryRow
            label="Refinance Cost"
            value={formatCurrency(data.refinanceCost)}
            highlight="negative"
          />
        </div>

        {/* Loan Term Impact */}
        <div className="pt-4">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Loan Term</h3>
          <SummaryRow
            label="Original Remaining Term"
            value={formatMonths(data.originalRemainingTerm)}
          />
          <SummaryRow
            label="New Loan Term"
            value={formatMonths(data.refiTerm)}
          />
          <SummaryRow
            label="Term Extension"
            value={termExtension > 0 ? `+${formatMonths(termExtension)}` : termExtension < 0 ? `-${formatMonths(Math.abs(termExtension))}` : 'No change'}
            highlight={termExtension > 0 ? 'negative' : termExtension < 0 ? 'positive' : 'neutral'}
            subtext={termExtension > 0 ? 'Loan will be paid off later' : termExtension < 0 ? 'Loan will be paid off sooner' : undefined}
          />
        </div>
      </dl>
    </div>
  );
}
