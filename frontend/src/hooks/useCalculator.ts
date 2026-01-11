/**
 * React Query hook for calculator API with debouncing support
 */

import { useMutation } from '@tanstack/react-query';
import { useDebouncedCallback } from 'use-debounce';
import { useCallback, useState, useRef, useEffect } from 'react';
import { calculateRefinance } from '../api/calculator';
import type { CalculatorRequest, CalculatorResponse } from '../types/calculator';
import type { CalculatorFormData } from '../types/forms';

interface UseCalculatorOptions {
  debounceMs?: number;
  onSuccess?: (data: CalculatorResponse) => void;
  onError?: (error: Error) => void;
}

interface UseCalculatorResult {
  results: CalculatorResponse | null;
  isLoading: boolean;
  error: Error | null;
  calculate: (data: CalculatorFormData) => void;
  calculateImmediate: (data: CalculatorFormData) => void;
  reset: () => void;
}

/**
 * Transform form data to API request format
 */
function transformFormData(data: CalculatorFormData): CalculatorRequest {
  return {
    mortgage: {
      originalPrincipal: data.mortgage.originalPrincipal,
      originalTerm: data.mortgage.originalTerm,
      originalInterestRate: data.mortgage.originalInterestRate,
      remainingPrincipal: data.mortgage.remainingPrincipal,
      remainingTerm: data.mortgage.remainingTerm,
    },
    refinance: {
      targetTerm: data.refinance.targetTerm,
      targetMonthlyPayment: data.refinance.targetMonthlyPayment,
      targetInterestRate: data.refinance.targetInterestRate,
      estimatedRefinanceCost: data.refinance.estimatedRefinanceCost,
    },
  };
}

export function useCalculator(options: UseCalculatorOptions = {}): UseCalculatorResult {
  const { debounceMs = 500, onSuccess, onError } = options;

  const [results, setResults] = useState<CalculatorResponse | null>(null);
  const pendingRequestRef = useRef<AbortController | null>(null);

  const mutation = useMutation({
    mutationFn: async (data: CalculatorRequest) => {
      // Cancel any pending request
      if (pendingRequestRef.current) {
        pendingRequestRef.current.abort();
      }

      pendingRequestRef.current = new AbortController();
      return calculateRefinance(data);
    },
    onSuccess: (data) => {
      setResults(data);
      onSuccess?.(data);
    },
    onError: (error: Error) => {
      onError?.(error);
    },
  });

  // Debounced calculation for auto-calculation on form changes
  const debouncedCalculate = useDebouncedCallback(
    (data: CalculatorFormData) => {
      const request = transformFormData(data);
      mutation.mutate(request);
    },
    debounceMs
  );

  // Immediate calculation for explicit button click
  const calculateImmediate = useCallback(
    (data: CalculatorFormData) => {
      debouncedCalculate.cancel();
      const request = transformFormData(data);
      mutation.mutate(request);
    },
    [mutation, debouncedCalculate]
  );

  // Debounced calculation (for auto-calc on input changes)
  const calculate = useCallback(
    (data: CalculatorFormData) => {
      debouncedCalculate(data);
    },
    [debouncedCalculate]
  );

  // Reset results and cancel any pending requests
  const reset = useCallback(() => {
    debouncedCalculate.cancel();
    if (pendingRequestRef.current) {
      pendingRequestRef.current.abort();
    }
    setResults(null);
    mutation.reset();
  }, [debouncedCalculate, mutation]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      debouncedCalculate.cancel();
      if (pendingRequestRef.current) {
        pendingRequestRef.current.abort();
      }
    };
  }, [debouncedCalculate]);

  return {
    results,
    isLoading: mutation.isPending,
    error: mutation.error,
    calculate,
    calculateImmediate,
    reset,
  };
}
