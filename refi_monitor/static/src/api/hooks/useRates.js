/**
 * React Query hooks for mortgage rate operations.
 */
import { useQuery } from '@tanstack/react-query';
import api from '../client';

export const rateKeys = {
  all: ['rates'],
  current: () => [...rateKeys.all, 'current'],
  currentFiltered: (filters) => [...rateKeys.current(), filters],
  history: () => [...rateKeys.all, 'history'],
  historyFiltered: (filters) => [...rateKeys.history(), filters],
};

/**
 * Fetch current mortgage rates.
 * @param {Object} options
 * @param {string} options.zipCode - Zip code to fetch rates for (optional)
 * @param {number} options.termMonths - Term in months (e.g., 360 for 30-year) (optional)
 */
export function useCurrentRates({ zipCode, termMonths } = {}) {
  return useQuery({
    queryKey: rateKeys.currentFiltered({ zipCode, termMonths }),
    queryFn: () => {
      const params = new URLSearchParams();
      if (zipCode) params.append('zip_code', zipCode);
      if (termMonths) params.append('term_months', termMonths);
      const queryString = params.toString();
      const endpoint = queryString ? `/rates/current?${queryString}` : '/rates/current';
      return api.get(endpoint);
    },
    staleTime: 1000 * 60 * 15, // 15 minutes - rates don't change frequently
  });
}

/**
 * Fetch historical mortgage rate data.
 * @param {Object} options
 * @param {string} options.zipCode - Zip code to fetch rates for (optional)
 * @param {number} options.termMonths - Term in months (required, defaults to 360)
 * @param {number} options.days - Number of days of history (optional, default 30)
 */
export function useRateHistory({ zipCode, termMonths = 360, days = 30 } = {}) {
  return useQuery({
    queryKey: rateKeys.historyFiltered({ zipCode, termMonths, days }),
    queryFn: () => {
      const params = new URLSearchParams();
      if (zipCode) params.append('zip_code', zipCode);
      params.append('term_months', termMonths);
      params.append('days', days);
      return api.get(`/rates/history?${params.toString()}`);
    },
    staleTime: 1000 * 60 * 30, // 30 minutes - historical data changes slowly
  });
}
