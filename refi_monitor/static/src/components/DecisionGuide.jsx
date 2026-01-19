import React from 'react';
import { cn } from '../lib/utils';

/**
 * Decision recommendation item with icon and description.
 */
function RecommendationItem({ icon, title, description, status }) {
  const statusColors = {
    positive: 'text-green-400 bg-green-900/30 border-green-700',
    neutral: 'text-blue-400 bg-blue-900/30 border-blue-700',
    negative: 'text-red-400 bg-red-900/30 border-red-700',
    warning: 'text-yellow-400 bg-yellow-900/30 border-yellow-700',
  };

  const colorClass = statusColors[status] || statusColors.neutral;

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg border',
        colorClass
      )}
    >
      <div className="flex-shrink-0 mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-gray-200">{title}</p>
        <p className="text-xs text-gray-400 mt-0.5">{description}</p>
      </div>
    </div>
  );
}

/**
 * Icons for different recommendation types
 */
const Icons = {
  checkCircle: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  clock: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  alertTriangle: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  trendingDown: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
    </svg>
  ),
  trendingUp: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  dollarSign: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

/**
 * Generate recommendations based on refi data
 */
function generateRecommendations(data) {
  const recommendations = [];
  const { refiScore, rateDifference, breakEvenMonths, monthlySavings } = data;

  // Score-based primary recommendation
  if (refiScore >= 80) {
    recommendations.push({
      icon: Icons.checkCircle,
      title: 'Strong Refinance Opportunity',
      description: 'Market conditions are favorable. Consider contacting lenders to lock in current rates.',
      status: 'positive',
    });
  } else if (refiScore >= 60) {
    recommendations.push({
      icon: Icons.clock,
      title: 'Good Opportunity - Monitor Closely',
      description: 'Conditions are improving. Continue monitoring for the optimal entry point.',
      status: 'neutral',
    });
  } else if (refiScore >= 40) {
    recommendations.push({
      icon: Icons.clock,
      title: 'Wait for Better Conditions',
      description: 'Current conditions are fair. Set up alerts to be notified when rates improve.',
      status: 'warning',
    });
  } else {
    recommendations.push({
      icon: Icons.alertTriangle,
      title: 'Not Recommended at This Time',
      description: 'Refinancing now may not provide significant benefit. Continue monitoring.',
      status: 'negative',
    });
  }

  // Rate difference insight
  if (rateDifference !== undefined) {
    if (rateDifference >= 0.75) {
      recommendations.push({
        icon: Icons.trendingDown,
        title: `${rateDifference.toFixed(2)}% Rate Reduction Available`,
        description: 'Significant rate decrease available compared to your current mortgage.',
        status: 'positive',
      });
    } else if (rateDifference >= 0.25) {
      recommendations.push({
        icon: Icons.trendingDown,
        title: `${rateDifference.toFixed(2)}% Rate Reduction`,
        description: 'Moderate rate improvement available. Factor in closing costs.',
        status: 'neutral',
      });
    } else if (rateDifference > 0) {
      recommendations.push({
        icon: Icons.alertTriangle,
        title: 'Minimal Rate Difference',
        description: 'Small rate reduction may not offset refinancing costs.',
        status: 'warning',
      });
    }
  }

  // Break-even analysis
  if (breakEvenMonths !== undefined && breakEvenMonths > 0) {
    if (breakEvenMonths <= 18) {
      recommendations.push({
        icon: Icons.dollarSign,
        title: `${breakEvenMonths} Month Break-Even`,
        description: 'Quick payback period. Favorable if you plan to stay in your home.',
        status: 'positive',
      });
    } else if (breakEvenMonths <= 36) {
      recommendations.push({
        icon: Icons.dollarSign,
        title: `${breakEvenMonths} Month Break-Even`,
        description: 'Reasonable payback. Ensure you plan to stay at least this long.',
        status: 'neutral',
      });
    } else {
      recommendations.push({
        icon: Icons.dollarSign,
        title: `${breakEvenMonths} Month Break-Even`,
        description: 'Extended payback period. Consider if you\'ll stay long enough to benefit.',
        status: 'warning',
      });
    }
  }

  // Monthly savings insight
  if (monthlySavings !== undefined && monthlySavings > 0) {
    recommendations.push({
      icon: Icons.trendingUp,
      title: `$${monthlySavings.toLocaleString()} Monthly Savings`,
      description: 'Estimated reduction in your monthly mortgage payment.',
      status: monthlySavings >= 200 ? 'positive' : 'neutral',
    });
  }

  return recommendations;
}

/**
 * DecisionGuide - Provides actionable refinancing recommendations.
 *
 * Analyzes current market conditions and user's mortgage data to
 * generate personalized guidance on whether to refinance.
 *
 * @param {Object} props
 * @param {number} props.refiScore - Refinance opportunity score (0-100)
 * @param {number} props.rateDifference - Difference between current and market rate
 * @param {number} props.breakEvenMonths - Months to break even on refi costs
 * @param {number} props.monthlySavings - Estimated monthly savings
 * @param {Array} props.customRecommendations - Override with custom recommendations
 * @param {string} props.title - Component title
 * @param {string} props.className - Additional CSS classes
 */
function DecisionGuide({
  refiScore = 0,
  rateDifference,
  breakEvenMonths,
  monthlySavings,
  customRecommendations,
  title = 'Refinance Decision Guide',
  className,
}) {
  const recommendations =
    customRecommendations ||
    generateRecommendations({
      refiScore,
      rateDifference,
      breakEvenMonths,
      monthlySavings,
    });

  return (
    <div
      className={cn(
        'bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 shadow-lg',
        className
      )}
    >
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>

      <div className="space-y-3">
        {recommendations.map((rec, index) => (
          <RecommendationItem
            key={index}
            icon={rec.icon}
            title={rec.title}
            description={rec.description}
            status={rec.status}
          />
        ))}
      </div>

      {recommendations.length === 0 && (
        <p className="text-gray-500 text-sm text-center py-4">
          Add mortgage data to receive personalized recommendations.
        </p>
      )}
    </div>
  );
}

export default DecisionGuide;
