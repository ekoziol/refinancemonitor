/**
 * API client for making requests to the Flask backend.
 * Provides a consistent interface for all API calls with error handling.
 */

const API_BASE = '/api';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function handleResponse(response) {
  const data = await response.json();

  if (!response.ok) {
    throw new ApiError(
      data.error || 'An error occurred',
      response.status,
      data
    );
  }

  return data;
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);
  return handleResponse(response);
}

export const api = {
  get: (endpoint) => request(endpoint, { method: 'GET' }),

  post: (endpoint, data) => request(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  put: (endpoint, data) => request(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  patch: (endpoint, data) => request(endpoint, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),

  delete: (endpoint) => request(endpoint, { method: 'DELETE' }),
};

export { ApiError };
export default api;
