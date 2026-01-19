import React from 'react';
import { cn } from '../lib/utils';

/**
 * Format currency value for display
 */
function formatCurrency(value, showSign = false) {
  if (value === undefined || value === null) return '--';
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(Math.abs(value));

  if (showSign && value !== 0) {
    return value > 0 ? `+${formatted}` : `-${formatted}`;
  }
  return formatted;
}

/**
 * Individual impact metric row
 */
function ImpactRow({ label, currentValue, newValue, difference, highlight }) {
  const isPositive = difference > 0;
  const isNegative = difference < 0;

  return (
    <div
      className={cn(
        'grid grid-cols-4 gap-2 py-3 px-2 rounded-lg',
        highlight && 'bg-gray-800/50'
      )}
    >
      <div className="text-sm text-gray-400">{label}</div>
      <div className="text-sm text-gray-300 text-right">
        {formatCurrency(currentValue)}
      </div>
      <div className="text-sm text-gray-300 text-right">
        {formatCurrency(newValue)}
      </div>
      <div
        className={cn(
          'text-sm font-medium text-right',
          isPositive && 'text-green-400',
          isNegative && 'text-red-400',
          !isPositive && !isNegative && 'text-gray-400'
        )}
      >
        {formatCurrency(difference, true)}
      </div>
    </div>
  );
}

/**
 * Summary stat card
 */
function SummaryStat({ label, value, subtext, variant = 'default' }) {
  const variants = {
    default: 'from-gray-800 to-gray-700',
    positive: 'from-green-900 to-green-800',
    negative: 'from-red-900 to-red-800',
    highlight: 'from-blue-900 to-blue-800',
  };

  return (
    <div
      className={cn(
        'bg-gradient-to-br rounded-lg p-4 text-center',
        variants[variant]
      )}
    >
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-gray-300 mt-1">{label}</div>
      {subtext && <div className="text-xs text-gray-500 mt-0.5">{subtext}</div>}
    </div>
  );
}

/**
 * FinancialImpact - Comprehensive financial impact summary for refinancing.
 *
 * Displays a detailed comparison of current vs. refinanced mortgage costs
 * with monthly, annual, and lifetime savings projections.
 *
 * @param {Object} props
 * @param {number} props.currentMonthlyPayment - Current monthly mortgage payment
 * @param {number} props.newMonthlyPayment - Projected payment after refinancing
 * @param {number} props.currentRate - Current interest rate (decimal, e.g., 0.065)
 * @param {number} props.newRate - New interest rate (decimal)
 * @param {number} props.closingCosts - Estimated closing costs for refinance
 * @param {number} props.remainingMonths - Months remaining on current mortgage
 * @param {number} props.newTermMonths - Term of new mortgage in months
 * @param {number} props.loanBalance - Current loan balance
 * @param {string} props.title - Component title
 * @param {string} props.className - Additional CSS classes
 */
function FinancialImpact({
  currentMonthlyPayment,
  newMonthlyPayment,
  currentRate,
  newRate,
  closingCosts = 0,
  remainingMonths = 360,
  newTermMonths = 360,
  loanBalance,
  title = 'Financial Impact Summary',
  className,
}) {
  // Calculate derived values
  const monthlySavings =
    currentMonthlyPayment && newMonthlyPayment
      ? currentMonthlyPayment - newMonthlyPayment
      : null;

  const annualSavings = monthlySavings ? monthlySavings * 12 : null;

  // Calculate lifetime savings (using shorter of remaining or new term)
  const effectiveMonths = Math.min(remainingMonths, newTermMonths);
  const lifetimeSavings = monthlySavings ? monthlySavings * effectiveMonths : null;

  // Calculate break-even months
  const breakEvenMonths =
    monthlySavings && monthlySavings > 0 && closingCosts > 0
      ? Math.ceil(closingCosts / monthlySavings)
      : null;

  // Net savings (lifetime savings minus closing costs)
  const netSavings = lifetimeSavings ? lifetimeSavings - closingCosts : null;

  // Total interest calculations
  const currentTotalInterest =
    currentMonthlyPayment && remainingMonths
      ? currentMonthlyPayment * remainingMonths - (loanBalance || 0)
      : null;

  const newTotalInterest =
    newMonthlyPayment && newTermMonths
      ? newMonthlyPayment * newTermMonths - (loanBalance || 0)
      : null;

  const interestSavings =
    currentTotalInterest && newTotalInterest
      ? currentTotalInterest - newTotalInterest
      : null;

  // Rate difference
  const rateDifference =
    currentRate !== undefined && newRate !== undefined
      ? (currentRate - newRate) * 100
      : null;

  const hasData = currentMonthlyPayment !== undefined && newMonthlyPayment !== undefined;

  return (
    <div
      className={cn(
        'bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 shadow-lg',
        className
      )}
    >
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>

      {!hasData ? (
        <p className="text-gray-500 text-sm text-center py-8">
          Add mortgage data to see financial impact analysis.
        </p>
      ) : (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            <SummaryStat
              label="Monthly Savings"
              value={formatCurrency(monthlySavings)}
              variant={monthlySavings > 0 ? 'positive' : 'default'}
            />
            <SummaryStat
              label="Annual Savings"
              value={formatCurrency(annualSavings)}
              variant={annualSavings > 0 ? 'positive' : 'default'}
            />
            <SummaryStat
              label="Break-Even"
              value={breakEvenMonths ? `${breakEvenMonths} mo` : '--'}
              subtext="to recoup costs"
              variant="highlight"
            />
            <SummaryStat
              label="Net Lifetime Savings"
              value={formatCurrency(netSavings)}
              subtext="after closing costs"
              variant={netSavings > 0 ? 'positive' : netSavings < 0 ? 'negative' : 'default'}
            />
          </div>

          {/* Detailed Comparison Table */}
          <div className="border border-gray-700 rounded-lg overflow-hidden">
            {/* Header */}
            <div className="grid grid-cols-4 gap-2 py-2 px-2 bg-gray-800 text-xs font-medium text-gray-400">
              <div>Metric</div>
              <div className="text-right">Current</div>
              <div className="text-right">After Refi</div>
              <div className="text-right">Difference</div>
            </div>

            {/* Rows */}
            <div className="divide-y divide-gray-700/50">
              <ImpactRow
                label="Monthly Payment"
                currentValue={currentMonthlyPayment}
                newValue={newMonthlyPayment}
                difference={monthlySavings}
                highlight
              />

              {rateDifference !== null && (
                <div className="grid grid-cols-4 gap-2 py-3 px-2">
                  <div className="text-sm text-gray-400">Interest Rate</div>
                  <div className="text-sm text-gray-300 text-right">
                    {currentRate !== undefined ? `${(currentRate * 100).toFixed(2)}%` : '--'}
                  </div>
                  <div className="text-sm text-gray-300 text-right">
                    {newRate !== undefined ? `${(newRate * 100).toFixed(2)}%` : '--'}
                  </div>
                  <div
                    className={cn(
                      'text-sm font-medium text-right',
                      rateDifference > 0 && 'text-green-400',
                      rateDifference < 0 && 'text-red-400'
                    )}
                  >
                    {rateDifference > 0 ? '-' : '+'}{Math.abs(rateDifference).toFixed(2)}%
                  </div>
                </div>
              )}

              {interestSavings !== null && (
                <ImpactRow
                  label="Total Interest"
                  currentValue={currentTotalInterest}
                  newValue={newTotalInterest}
                  difference={interestSavings}
                />
              )}

              {closingCosts > 0 && (
                <div className="grid grid-cols-4 gap-2 py-3 px-2 bg-gray-800/30">
                  <div className="text-sm text-gray-400">Closing Costs</div>
                  <div className="text-sm text-gray-500 text-right">--</div>
                  <div className="text-sm text-red-400 text-right">
                    {formatCurrency(closingCosts)}
                  </div>
                  <div className="text-sm text-red-400 text-right">
                    -{formatCurrency(closingCosts)}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer Note */}
          <p className="text-xs text-gray-500 mt-4 text-center">
            * Estimates based on current data. Actual savings may vary based on final loan terms.
          </p>
        </>
      )}
    </div>
  );
}

export default FinancialImpact;
