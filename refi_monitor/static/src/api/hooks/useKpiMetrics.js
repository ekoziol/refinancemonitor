/**
 * React Query hooks for KPI metrics.
 */
import { useQuery } from '@tanstack/react-query';
import api from '../client';

export const kpiKeys = {
  all: ['kpi-metrics'],
  byMortgage: (mortgageId) => [...kpiKeys.all, mortgageId],
};

export function useKpiMetrics(mortgageId) {
  return useQuery({
    queryKey: kpiKeys.byMortgage(mortgageId),
    queryFn: () => {
      const endpoint = mortgageId
        ? `/kpi-metrics?mortgage_id=${mortgageId}`
        : '/kpi-metrics';
      return api.get(endpoint);
    },
  });
}
