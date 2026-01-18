/**
 * React Query hooks for mortgage operations.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../client';

export const mortgageKeys = {
  all: ['mortgages'],
  lists: () => [...mortgageKeys.all, 'list'],
  list: (filters) => [...mortgageKeys.lists(), filters],
  details: () => [...mortgageKeys.all, 'detail'],
  detail: (id) => [...mortgageKeys.details(), id],
};

export function useMortgages() {
  return useQuery({
    queryKey: mortgageKeys.lists(),
    queryFn: () => api.get('/mortgages'),
  });
}

export function useMortgage(mortgageId) {
  return useQuery({
    queryKey: mortgageKeys.detail(mortgageId),
    queryFn: () => api.get(`/mortgages/${mortgageId}`),
    enabled: !!mortgageId,
  });
}

export function useCreateMortgage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => api.post('/mortgages', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mortgageKeys.lists() });
    },
  });
}

export function useUpdateMortgage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => api.put(`/mortgages/${id}`, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: mortgageKeys.lists() });
      queryClient.invalidateQueries({ queryKey: mortgageKeys.detail(variables.id) });
    },
  });
}

export function useDeleteMortgage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => api.delete(`/mortgages/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mortgageKeys.lists() });
    },
  });
}
