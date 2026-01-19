/**
 * React Query hooks for timeline data.
 */
import { useQuery } from '@tanstack/react-query';
import api from '../client';

export const timelineKeys = {
  all: ['timeline'],
  byMortgage: (mortgageId, forecastDays) => [...timelineKeys.all, { mortgageId, forecastDays }],
};

/**
 * Fetch timeline data for visualization.
 * @param {Object} options
 * @param {number} options.mortgageId - Mortgage ID (optional, uses first mortgage if not provided)
 * @param {number} options.forecastDays - Number of days to forecast (default 30)
 */
export function useTimeline({ mortgageId, forecastDays = 30 } = {}) {
  return useQuery({
    queryKey: timelineKeys.byMortgage(mortgageId, forecastDays),
    queryFn: () => {
      const params = new URLSearchParams();
      if (mortgageId) params.append('mortgage_id', mortgageId);
      params.append('forecast_days', forecastDays);
      return api.get(`/timeline?${params.toString()}`);
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}
