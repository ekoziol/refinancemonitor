/**
 * React Query hooks for user operations.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../client';

export const userKeys = {
  all: ['user'],
  current: () => [...userKeys.all, 'current'],
};

export function useUser() {
  return useQuery({
    queryKey: userKeys.current(),
    queryFn: () => api.get('/user'),
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => api.put('/user', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.current() });
    },
  });
}
