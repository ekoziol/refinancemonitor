/**
 * API module exports.
 * Provides the API client, React Query hooks, and QueryProvider.
 */
export { default as api, ApiError } from './client';
export * from './hooks';
export { QueryProvider, queryClient } from './QueryProvider';
