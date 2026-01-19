/**
 * RefiTriggerPoint component for refinance decision support.
 *
 * Displays a visual recommendation based on market conditions,
 * user's current rate, potential savings, and refi score.
 */
import * as React from 'react';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

/**
 * Get score color classes based on score value.
 * @param {number} score - Score 0-100
 * @returns {Object} - Color classes for various elements
 */
function getScoreColors(score) {
  if (score >= 70) {
    return {
      badge: 'bg-green-100 text-green-800 border-green-200',
      progress: 'bg-green-500',
      text: 'text-green-600',
      glow: 'shadow-green-500/20',
    };
  }
  if (score >= 50) {
    return {
      badge: 'bg-blue-100 text-blue-800 border-blue-200',
      progress: 'bg-blue-500',
      text: 'text-blue-600',
      glow: 'shadow-blue-500/20',
    };
  }
  if (score >= 30) {
    return {
      badge: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      progress: 'bg-yellow-500',
      text: 'text-yellow-600',
      glow: 'shadow-yellow-500/20',
    };
  }
  return {
    badge: 'bg-gray-100 text-gray-600 border-gray-200',
    progress: 'bg-gray-400',
    text: 'text-gray-600',
    glow: 'shadow-gray-500/10',
  };
}

/**
 * Get recommendation text based on score and conditions.
 * @param {number} score
 * @param {number} rateDiff - Difference between current and market rate
 * @param {number} monthlySavings
 * @returns {Object} - headline, description, and action text
 */
function getRecommendation(score, rateDiff, monthlySavings) {
  if (score >= 70) {
    return {
      headline: 'Excellent Time to Refinance',
      description: `Current market rates are ${(rateDiff * 100).toFixed(2)}% lower than your rate. You could save ${formatCurrency(monthlySavings)} monthly.`,
      action: 'Set Alert Now',
      urgency: 'high',
    };
  }
  if (score >= 50) {
    return {
      headline: 'Good Refinance Opportunity',
      description: `Market conditions are favorable. Potential monthly savings of ${formatCurrency(monthlySavings)}.`,
      action: 'Consider Setting Alert',
      urgency: 'medium',
    };
  }
  if (score >= 30) {
    return {
      headline: 'Monitor Market Conditions',
      description: 'Rates are close to your current rate. Set an alert to be notified when conditions improve.',
      action: 'Set Rate Alert',
      urgency: 'low',
    };
  }
  return {
    headline: 'Current Rate is Competitive',
    description: 'Your current rate is at or below market rates. No immediate refinancing recommended.',
    action: 'Track Market',
    urgency: 'none',
  };
}

/**
 * Format currency for display.
 */
function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '--';
  return `$${parseFloat(amount).toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}

/**
 * Calculate break-even months.
 * @param {number} monthlySavings
 * @param {number} refiCost - Estimated refinance cost
 * @returns {number|null}
 */
function calculateBreakEven(monthlySavings, refiCost = 5000) {
  if (!monthlySavings || monthlySavings <= 0) return null;
  return Math.ceil(refiCost / monthlySavings);
}

/**
 * Score gauge component - visual indicator of refi score.
 */
function ScoreGauge({ score, label }) {
  const colors = getScoreColors(score);
  const normalizedScore = Math.min(100, Math.max(0, score || 0));

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`relative w-24 h-24 rounded-full shadow-lg ${colors.glow}`}>
        {/* Background circle */}
        <div className="absolute inset-0 rounded-full bg-muted" />

        {/* Progress arc - simplified as filled circle segment */}
        <svg
          className="absolute inset-0 w-full h-full -rotate-90"
          viewBox="0 0 100 100"
        >
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-muted"
          />
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeDasharray={`${normalizedScore * 2.51} 251`}
            strokeLinecap="round"
            className={colors.text}
          />
        </svg>

        {/* Center score display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-2xl font-bold ${colors.text}`}>
            {score ?? '--'}
          </span>
        </div>
      </div>
      <Badge className={colors.badge}>{label}</Badge>
    </div>
  );
}

/**
 * Stat row component for displaying metrics.
 */
function StatRow({ label, value, highlight = false }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-border last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={`text-sm font-medium ${highlight ? 'text-green-600' : 'text-foreground'}`}>
        {value}
      </span>
    </div>
  );
}

/**
 * RefiTriggerPoint - Decision support component for refinance recommendations.
 *
 * @param {Object} props
 * @param {number} [props.currentRate] - User's current mortgage rate (decimal)
 * @param {number} [props.marketRate] - Current market rate (decimal)
 * @param {number} [props.monthlySavings] - Potential monthly savings
 * @param {number} [props.refiScore] - Refinance score 0-100
 * @param {string} [props.refiScoreLabel] - Score label (Excellent, Good, etc.)
 * @param {number} [props.estimatedRefiCost] - Estimated refinance closing cost
 * @param {string} [props.mortgageName] - Name of the mortgage
 * @param {Function} [props.onSetAlert] - Callback when set alert is clicked
 * @param {boolean} [props.isLoading] - Show loading state
 */
export default function RefiTriggerPoint({
  currentRate,
  marketRate,
  monthlySavings,
  refiScore,
  refiScoreLabel = 'N/A',
  estimatedRefiCost = 5000,
  mortgageName,
  onSetAlert,
  isLoading = false,
}) {
  // Loading skeleton
  if (isLoading) {
    return (
      <Card className="w-full animate-pulse">
        <CardHeader>
          <div className="h-6 w-48 bg-muted rounded" />
          <div className="h-4 w-64 bg-muted rounded mt-2" />
        </CardHeader>
        <CardContent>
          <div className="flex gap-8">
            <div className="h-24 w-24 bg-muted rounded-full" />
            <div className="flex-1 space-y-3">
              <div className="h-4 w-full bg-muted rounded" />
              <div className="h-4 w-3/4 bg-muted rounded" />
              <div className="h-4 w-1/2 bg-muted rounded" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Handle missing data
  const hasData = refiScore !== null && refiScore !== undefined;
  if (!hasData) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Refinance Decision Support</CardTitle>
          <CardDescription>
            Add a mortgage to see your refinance recommendation
          </CardDescription>
        </CardHeader>
        <CardContent className="py-8 text-center text-muted-foreground">
          No mortgage data available for analysis
        </CardContent>
      </Card>
    );
  }

  const rateDiff = (currentRate || 0) - (marketRate || 0);
  const recommendation = getRecommendation(refiScore, rateDiff, monthlySavings);
  const breakEvenMonths = calculateBreakEven(monthlySavings, estimatedRefiCost);
  const colors = getScoreColors(refiScore);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>Refinance Decision Support</CardTitle>
            <CardDescription>
              {mortgageName ? `Analysis for ${mortgageName}` : 'Based on your mortgage data'}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="flex flex-col md:flex-row gap-6">
          {/* Score Gauge */}
          <div className="flex justify-center md:justify-start">
            <ScoreGauge score={refiScore} label={refiScoreLabel} />
          </div>

          {/* Recommendation Content */}
          <div className="flex-1 space-y-4">
            {/* Headline */}
            <div>
              <h3 className={`text-lg font-semibold ${colors.text}`}>
                {recommendation.headline}
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                {recommendation.description}
              </p>
            </div>

            {/* Stats */}
            <div className="bg-muted/50 rounded-lg p-4">
              <StatRow
                label="Your Rate"
                value={currentRate ? `${(currentRate * 100).toFixed(2)}%` : '--'}
              />
              <StatRow
                label="Market Rate"
                value={marketRate ? `${(marketRate * 100).toFixed(2)}%` : '--'}
              />
              <StatRow
                label="Potential Savings"
                value={formatCurrency(monthlySavings) + '/mo'}
                highlight={monthlySavings > 0}
              />
              {breakEvenMonths && (
                <StatRow
                  label="Break-Even Point"
                  value={`${breakEvenMonths} months`}
                />
              )}
            </div>

            {/* Action Button */}
            {onSetAlert && recommendation.urgency !== 'none' && (
              <Button
                onClick={onSetAlert}
                variant={recommendation.urgency === 'high' ? 'default' : 'outline'}
                className="w-full md:w-auto"
              >
                {recommendation.action}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
