import React from 'react';
import { useKpiMetrics } from '../api';

/**
 * Individual metric card component displaying a single KPI value.
 *
 * @param {Object} props
 * @param {string} props.title - Card title/label
 * @param {string} props.value - Display value
 * @param {string} props.subtitle - Optional subtitle text
 * @param {string} props.colorClass - Tailwind gradient class for card color
 * @param {React.ReactNode} props.icon - Optional icon element
 */
function MetricCard({ title, value, subtitle, colorClass = 'from-gray-800 to-gray-700', icon }) {
  return (
    <div className={`bg-gradient-to-r flex-auto ${colorClass} shadow-lg rounded-lg`}>
      <div className="md:p-7 p-4">
        {icon && <div className="flex justify-center mb-2">{icon}</div>}
        <h2 className="text-2xl text-center text-gray-200 capitalize font-semibold">
          {value}
        </h2>
        <h3 className="text-sm text-gray-400 text-center">{title}</h3>
        {subtitle && (
          <p className="text-xs text-gray-500 text-center mt-1">{subtitle}</p>
        )}
      </div>
    </div>
  );
}

/**
 * Score badge component for the refi score display.
 */
function ScoreBadge({ score, label }) {
  let badgeColor;
  if (score >= 70) {
    badgeColor = 'bg-green-100 text-green-800';
  } else if (score >= 50) {
    badgeColor = 'bg-blue-100 text-blue-800';
  } else if (score >= 30) {
    badgeColor = 'bg-yellow-100 text-yellow-800';
  } else {
    badgeColor = 'bg-gray-100 text-gray-800';
  }

  return (
    <span className={`px-3 py-1 text-sm font-medium rounded-full ${badgeColor}`}>
      {score} - {label}
    </span>
  );
}

const defaultMetrics = {
  market_rate_display: '--',
  your_rate_display: '--',
  monthly_savings_display: '--',
  refi_score: null,
  refi_score_label: 'N/A'
};

/**
 * MetricCards component displaying KPI dashboard cards for:
 * - Market Rate: Current market mortgage rate
 * - Your Rate: User's current mortgage rate
 * - Savings: Potential monthly savings from refinancing
 * - Refi Score: Score indicating refinance opportunity (0-100)
 *
 * @param {Object} props
 * @param {number} props.mortgageId - Optional mortgage ID to fetch metrics for
 * @param {Object} props.initialData - Optional initial data to display before fetch
 */
function MetricCards({ mortgageId, initialData }) {
  const { data, isLoading, error } = useKpiMetrics(mortgageId);
  const metrics = data || initialData || defaultMetrics;

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gradient-to-r from-gray-800 to-gray-700 shadow-lg rounded-lg animate-pulse">
            <div className="md:p-7 p-4">
              <div className="h-8 bg-gray-600 rounded mb-2"></div>
              <div className="h-4 bg-gray-600 rounded w-3/4 mx-auto"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 text-red-200 p-4 rounded-lg">
        Error loading metrics: {error.message}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Market Rate"
        value={metrics.market_rate_display}
        subtitle="30-Year Fixed"
        colorClass="from-blue-900 to-blue-800"
        icon={
          <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        }
      />

      <MetricCard
        title="Your Rate"
        value={metrics.your_rate_display}
        subtitle="Current Mortgage"
        colorClass="from-gray-800 to-gray-700"
        icon={
          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        }
      />

      <MetricCard
        title="Monthly Savings"
        value={metrics.monthly_savings_display}
        subtitle="Potential savings/mo"
        colorClass="from-green-900 to-green-800"
        icon={
          <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
      />

      <div className="bg-gradient-to-r from-purple-900 to-purple-800 shadow-lg rounded-lg">
        <div className="md:p-7 p-4">
          <div className="flex justify-center mb-2">
            <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h2 className="text-2xl text-center text-gray-200 capitalize font-semibold">
            {metrics.refi_score !== null ? (
              <ScoreBadge score={metrics.refi_score} label={metrics.refi_score_label} />
            ) : (
              '--'
            )}
          </h2>
          <h3 className="text-sm text-gray-400 text-center">Refi Score</h3>
          <p className="text-xs text-gray-500 text-center mt-1">Refinance opportunity</p>
        </div>
      </div>
    </div>
  );
}

export default MetricCards;
