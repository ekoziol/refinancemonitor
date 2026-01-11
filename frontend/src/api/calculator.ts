/**
 * Calculator API functions
 */

import { apiClient } from './client';
import type { CalculatorRequest, CalculatorResponse } from '../types/calculator';

export async function calculateRefinance(
  data: CalculatorRequest
): Promise<CalculatorResponse> {
  return apiClient<CalculatorResponse>('/api/calculate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
