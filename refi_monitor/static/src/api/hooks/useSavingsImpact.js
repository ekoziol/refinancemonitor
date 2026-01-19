/**
 * React Query hooks for savings impact data.
 */
import { useQuery } from '@tanstack/react-query';
import api from '../client';

export const savingsImpactKeys = {
  all: ['savings-impact'],
  byParams: (params) => [...savingsImpactKeys.all, params],
};

/**
 * Fetch savings impact data comparing current mortgage vs refinance scenario.
 * @param {Object} options
 * @param {number} options.mortgageId - Mortgage ID (optional, uses first mortgage if not provided)
 * @param {number} options.targetRate - Target refinance rate (optional, defaults to market rate)
 * @param {number} options.targetTerm - Target refinance term in months (optional)
 * @param {number} options.refiCost - Estimated refinance closing costs (default 5000)
 */
export function useSavingsImpact({
  mortgageId,
  targetRate,
  targetTerm,
  refiCost = 5000,
} = {}) {
  return useQuery({
    queryKey: savingsImpactKeys.byParams({ mortgageId, targetRate, targetTerm, refiCost }),
    queryFn: () => {
      const params = new URLSearchParams();
      if (mortgageId) params.append('mortgage_id', mortgageId);
      if (targetRate !== undefined) params.append('target_rate', targetRate);
      if (targetTerm !== undefined) params.append('target_term', targetTerm);
      params.append('refi_cost', refiCost);
      return api.get(`/savings-impact?${params.toString()}`);
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
