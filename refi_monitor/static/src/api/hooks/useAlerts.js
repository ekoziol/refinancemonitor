/**
 * React Query hooks for alert operations.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../client';

export const alertKeys = {
  all: ['alerts'],
  lists: () => [...alertKeys.all, 'list'],
  list: (filters) => [...alertKeys.lists(), filters],
  details: () => [...alertKeys.all, 'detail'],
  detail: (id) => [...alertKeys.details(), id],
};

export function useAlerts() {
  return useQuery({
    queryKey: alertKeys.lists(),
    queryFn: () => api.get('/alerts'),
  });
}

export function useAlert(alertId) {
  return useQuery({
    queryKey: alertKeys.detail(alertId),
    queryFn: () => api.get(`/alerts/${alertId}`),
    enabled: !!alertId,
  });
}

export function useCreateAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => api.post('/alerts', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
    },
  });
}

export function useUpdateAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => api.put(`/alerts/${id}`, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      queryClient.invalidateQueries({ queryKey: alertKeys.detail(variables.id) });
    },
  });
}

export function useDeleteAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => api.delete(`/alerts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
    },
  });
}

export function usePauseAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => api.post(`/alerts/${id}/pause`),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      queryClient.invalidateQueries({ queryKey: alertKeys.detail(variables) });
    },
  });
}

export function useResumeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => api.post(`/alerts/${id}/resume`),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      queryClient.invalidateQueries({ queryKey: alertKeys.detail(variables) });
    },
  });
}
