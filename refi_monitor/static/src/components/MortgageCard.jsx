/**
 * MortgageCard component for displaying mortgage details with actions.
 *
 * Displays mortgage information in a glass-morphism styled card with
 * edit, delete, and view alerts functionality.
 */
import * as React from 'react';
import { Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

/**
 * Format currency value for display.
 * @param {number|null|undefined} amount
 * @returns {string}
 */
function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '--';
  return `$${parseFloat(amount).toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}

/**
 * Format interest rate as percentage.
 * @param {number|null|undefined} rate - Rate as decimal (e.g., 0.045 for 4.5%)
 * @returns {string}
 */
function formatRate(rate) {
  if (rate === null || rate === undefined) return '--';
  return `${(rate * 100).toFixed(2)}%`;
}

/**
 * Format term in months to years/months display.
 * @param {number|null|undefined} months
 * @returns {string}
 */
function formatTerm(months) {
  if (months === null || months === undefined) return '--';
  const years = Math.floor(months / 12);
  const remainingMonths = months % 12;
  if (remainingMonths === 0) return `${years} years`;
  if (years === 0) return `${remainingMonths} months`;
  return `${years}y ${remainingMonths}mo`;
}

/**
 * Get credit score badge styling based on score value.
 * @param {number|null|undefined} score
 * @returns {string}
 */
function getCreditScoreStyle(score) {
  if (score === null || score === undefined) return 'bg-gray-100 text-gray-600';
  if (score >= 750) return 'bg-green-100 text-green-800';
  if (score >= 700) return 'bg-blue-100 text-blue-800';
  if (score >= 650) return 'bg-yellow-100 text-yellow-800';
  return 'bg-red-100 text-red-800';
}

/**
 * Get credit score label based on score value.
 * @param {number|null|undefined} score
 * @returns {string}
 */
function getCreditScoreLabel(score) {
  if (score === null || score === undefined) return 'N/A';
  if (score >= 750) return 'Excellent';
  if (score >= 700) return 'Good';
  if (score >= 650) return 'Fair';
  return 'Poor';
}

/**
 * Stat display component for mortgage metrics.
 */
function MortgageStat({ label, value, className = '' }) {
  return (
    <div className={`flex flex-col ${className}`}>
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

/**
 * MortgageCard - Displays mortgage details with action buttons.
 *
 * @param {Object} props
 * @param {Object} props.mortgage - Mortgage data object
 * @param {number} props.mortgage.id - Mortgage ID
 * @param {string} props.mortgage.name - Mortgage name/label
 * @param {number} props.mortgage.remaining_principal - Remaining principal balance
 * @param {number} props.mortgage.remaining_term - Remaining term in months
 * @param {number} props.mortgage.original_interest_rate - Interest rate as decimal
 * @param {number} props.mortgage.credit_score - Credit score at origination
 * @param {number} [props.alertCount] - Number of active alerts for this mortgage
 * @param {boolean} [props.isSelected] - Whether this card is selected
 * @param {Function} [props.onSelect] - Callback when card is selected
 * @param {Function} [props.onEdit] - Callback when edit is clicked
 * @param {Function} [props.onDelete] - Callback when delete is clicked
 * @param {Function} [props.onViewAlerts] - Callback when view alerts is clicked
 * @param {boolean} [props.isLoading] - Show loading state
 */
export default function MortgageCard({
  mortgage,
  alertCount = 0,
  isSelected = false,
  onSelect,
  onEdit,
  onDelete,
  onViewAlerts,
  isLoading = false,
}) {
  // Loading skeleton
  if (isLoading) {
    return (
      <Card className="w-full animate-pulse">
        <CardHeader className="pb-3">
          <div className="h-5 w-32 bg-muted rounded" />
          <div className="h-4 w-24 bg-muted rounded mt-1" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-1">
                <div className="h-3 w-16 bg-muted rounded" />
                <div className="h-4 w-20 bg-muted rounded" />
              </div>
            ))}
          </div>
        </CardContent>
        <CardFooter className="pt-3 border-t">
          <div className="h-8 w-full bg-muted rounded" />
        </CardFooter>
      </Card>
    );
  }

  // Guard against missing mortgage data
  if (!mortgage) {
    return (
      <Card className="w-full">
        <CardContent className="py-8 text-center text-muted-foreground">
          No mortgage data available
        </CardContent>
      </Card>
    );
  }

  const creditScoreStyle = getCreditScoreStyle(mortgage.credit_score);
  const creditScoreLabel = getCreditScoreLabel(mortgage.credit_score);

  return (
    <Card
      className={`w-full transition-all duration-200 ${
        isSelected
          ? 'ring-2 ring-primary shadow-lg'
          : 'hover:shadow-md'
      } ${onSelect ? 'cursor-pointer' : ''}`}
      onClick={onSelect ? () => onSelect(mortgage.id) : undefined}
      role={onSelect ? 'button' : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onKeyDown={
        onSelect
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelect(mortgage.id);
              }
            }
          : undefined
      }
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <CardTitle className="text-lg truncate">{mortgage.name}</CardTitle>
            <CardDescription className="mt-1">
              ID: {mortgage.id}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2 ml-2">
            {alertCount > 0 && (
              <Badge variant="secondary" className="text-xs">
                {alertCount} alert{alertCount !== 1 ? 's' : ''}
              </Badge>
            )}
            <Badge className={creditScoreStyle}>
              {mortgage.credit_score || '--'} {creditScoreLabel}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <MortgageStat
            label="Principal"
            value={formatCurrency(mortgage.remaining_principal)}
          />
          <MortgageStat
            label="Remaining Term"
            value={formatTerm(mortgage.remaining_term)}
          />
          <MortgageStat
            label="Interest Rate"
            value={formatRate(mortgage.original_interest_rate)}
          />
          <MortgageStat
            label="Credit Score"
            value={mortgage.credit_score || '--'}
          />
        </div>
      </CardContent>

      <CardFooter className="flex justify-between gap-2 pt-3 border-t border-border">
        <div className="flex gap-2">
          {onViewAlerts && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onViewAlerts(mortgage.id);
              }}
            >
              View Alerts
            </Button>
          )}
        </div>

        <div className="flex gap-2">
          {onEdit && (
            <Button
              variant="secondary"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(mortgage.id);
              }}
            >
              Edit
            </Button>
          )}
          {onDelete && (
            <Button
              variant="destructive"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(mortgage.id);
              }}
            >
              Delete
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}
