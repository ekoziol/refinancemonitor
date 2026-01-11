/**
 * React Query hooks for calculator API
 * Provides loading states, caching, and automatic refetching
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import {
  calculateMonthlyPayment,
  getAmortizationSchedule,
  calculateBreakEven,
  calculateRecoup,
  findTargetRate,
  compareLoans,
  CompareLoansRequest,
  LoanComparisonResponse,
} from '../api/calculator';
import {
  CalculateLoanPaymentRequest,
  CalculateBreakEvenRequest,
  CalculateRecoupRequest,
  FindTargetRateRequest,
  MonthlyPaymentResponse,
  AmortizationScheduleResponse,
  BreakEvenAnalysisResponse,
  RecoupAnalysisResponse,
  TargetRateResponse,
} from '../types/calculator';

// Query keys for cache management
export const calculatorKeys = {
  all: ['calculator'] as const,
  monthlyPayment: (params: CalculateLoanPaymentRequest) =>
    [...calculatorKeys.all, 'monthlyPayment', params] as const,
  amortization: (params: CalculateLoanPaymentRequest) =>
    [...calculatorKeys.all, 'amortization', params] as const,
  breakEven: (params: CalculateBreakEvenRequest) =>
    [...calculatorKeys.all, 'breakEven', params] as const,
  recoup: (params: CalculateRecoupRequest) =>
    [...calculatorKeys.all, 'recoup', params] as const,
  targetRate: (params: FindTargetRateRequest) =>
    [...calculatorKeys.all, 'targetRate', params] as const,
  comparison: (params: CompareLoansRequest) =>
    [...calculatorKeys.all, 'comparison', params] as const,
};

/**
 * Hook for calculating monthly payment
 */
export function useMonthlyPayment(
  params: CalculateLoanPaymentRequest,
  options?: Omit<UseQueryOptions<MonthlyPaymentResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: calculatorKeys.monthlyPayment(params),
    queryFn: () => calculateMonthlyPayment(params),
    enabled: params.principal > 0 && params.rate > 0 && params.term > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Hook for getting amortization schedule
 */
export function useAmortizationSchedule(
  params: CalculateLoanPaymentRequest,
  options?: Omit<UseQueryOptions<AmortizationScheduleResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: calculatorKeys.amortization(params),
    queryFn: () => getAmortizationSchedule(params),
    enabled: params.principal > 0 && params.rate > 0 && params.term > 0,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Hook for break-even analysis
 */
export function useBreakEvenAnalysis(
  params: CalculateBreakEvenRequest,
  options?: Omit<UseQueryOptions<BreakEvenAnalysisResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: calculatorKeys.breakEven(params),
    queryFn: () => calculateBreakEven(params),
    enabled:
      params.originalPrincipal > 0 &&
      params.originalRate > 0 &&
      params.originalTerm > 0 &&
      params.newTerm > 0,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Hook for recoup analysis
 */
export function useRecoupAnalysis(
  params: CalculateRecoupRequest,
  options?: Omit<UseQueryOptions<RecoupAnalysisResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: calculatorKeys.recoup(params),
    queryFn: () => calculateRecoup(params),
    enabled:
      params.originalMonthlyPayment > 0 &&
      params.refiMonthlyPayment > 0 &&
      params.targetTerm > 0,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Hook for finding target rate
 */
export function useTargetRate(
  params: FindTargetRateRequest,
  options?: Omit<UseQueryOptions<TargetRateResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: calculatorKeys.targetRate(params),
    queryFn: () => findTargetRate(params),
    enabled: params.principal > 0 && params.term > 0 && params.targetPayment > 0,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Hook for comparing loan scenarios
 */
export function useLoanComparison(
  params: CompareLoansRequest,
  options?: Omit<UseQueryOptions<LoanComparisonResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: calculatorKeys.comparison(params),
    queryFn: () => compareLoans(params),
    enabled:
      params.currentLoan.principal > 0 &&
      params.currentLoan.rate > 0 &&
      params.newLoan.principal > 0 &&
      params.newLoan.rate > 0,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Mutation hook for calculating monthly payment (for form submissions)
 */
export function useCalculatePaymentMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: calculateMonthlyPayment,
    onSuccess: (data, variables) => {
      // Cache the result
      queryClient.setQueryData(calculatorKeys.monthlyPayment(variables), data);
    },
  });
}

/**
 * Mutation hook for break-even analysis (for form submissions)
 */
export function useBreakEvenMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: calculateBreakEven,
    onSuccess: (data, variables) => {
      queryClient.setQueryData(calculatorKeys.breakEven(variables), data);
    },
  });
}

/**
 * Mutation hook for loan comparison (for form submissions)
 */
export function useCompareLoans() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: compareLoans,
    onSuccess: (data, variables) => {
      queryClient.setQueryData(calculatorKeys.comparison(variables), data);
    },
  });
}

/**
 * Hook to invalidate all calculator caches
 */
export function useInvalidateCalculatorCache() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: calculatorKeys.all });
  };
}

/**
 * Combined hook for full refinance calculator workflow
 */
export function useRefinanceCalculator(params: {
  currentLoan: CalculateLoanPaymentRequest;
  newLoan: CalculateLoanPaymentRequest;
  refiCost: number;
}) {
  const currentPayment = useMonthlyPayment(params.currentLoan);
  const newPayment = useMonthlyPayment(params.newLoan);
  const comparison = useLoanComparison({
    currentLoan: params.currentLoan,
    newLoan: params.newLoan,
    refiCost: params.refiCost,
  });

  return {
    currentPayment,
    newPayment,
    comparison,
    isLoading:
      currentPayment.isLoading || newPayment.isLoading || comparison.isLoading,
    isError: currentPayment.isError || newPayment.isError || comparison.isError,
    error: currentPayment.error || newPayment.error || comparison.error,
  };
}

export default {
  useMonthlyPayment,
  useAmortizationSchedule,
  useBreakEvenAnalysis,
  useRecoupAnalysis,
  useTargetRate,
  useLoanComparison,
  useCalculatePaymentMutation,
  useBreakEvenMutation,
  useCompareLoans,
  useInvalidateCalculatorCache,
  useRefinanceCalculator,
  calculatorKeys,
};
