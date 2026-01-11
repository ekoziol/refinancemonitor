/**
 * Calculator API functions
 * Type-safe API calls for refinance calculations
 */

import { apiClient } from './client';
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

const CALCULATOR_ENDPOINT = '/calculator';

/**
 * Calculate monthly loan payment
 */
export async function calculateMonthlyPayment(
  request: CalculateLoanPaymentRequest
): Promise<MonthlyPaymentResponse> {
  return apiClient.post<MonthlyPaymentResponse>(
    `${CALCULATOR_ENDPOINT}/monthly-payment`,
    {
      principal: request.principal,
      rate: request.rate,
      term: request.term,
    }
  );
}

/**
 * Get full amortization schedule
 */
export async function getAmortizationSchedule(
  request: CalculateLoanPaymentRequest
): Promise<AmortizationScheduleResponse> {
  return apiClient.post<AmortizationScheduleResponse>(
    `${CALCULATOR_ENDPOINT}/amortization`,
    {
      principal: request.principal,
      rate: request.rate,
      term: request.term,
    }
  );
}

/**
 * Calculate break-even analysis for refinance
 */
export async function calculateBreakEven(
  request: CalculateBreakEvenRequest
): Promise<BreakEvenAnalysisResponse> {
  return apiClient.post<BreakEvenAnalysisResponse>(
    `${CALCULATOR_ENDPOINT}/break-even`,
    {
      original_principal: request.originalPrincipal,
      original_rate: request.originalRate,
      original_term: request.originalTerm,
      current_principal: request.currentPrincipal,
      term_remaining: request.termRemaining,
      new_term: request.newTerm,
      refi_cost: request.refiCost,
    }
  );
}

/**
 * Calculate time to recoup refinance costs
 */
export async function calculateRecoup(
  request: CalculateRecoupRequest
): Promise<RecoupAnalysisResponse> {
  return apiClient.post<RecoupAnalysisResponse>(
    `${CALCULATOR_ENDPOINT}/recoup`,
    {
      original_monthly_payment: request.originalMonthlyPayment,
      refi_monthly_payment: request.refiMonthlyPayment,
      target_term: request.targetTerm,
      refi_cost: request.refiCost,
    }
  );
}

/**
 * Find target interest rate for desired payment
 */
export async function findTargetRate(
  request: FindTargetRateRequest
): Promise<TargetRateResponse> {
  return apiClient.post<TargetRateResponse>(
    `${CALCULATOR_ENDPOINT}/target-rate`,
    {
      principal: request.principal,
      term: request.term,
      target_payment: request.targetPayment,
    }
  );
}

/**
 * Compare two loan scenarios
 */
export interface CompareLoansRequest {
  currentLoan: CalculateLoanPaymentRequest;
  newLoan: CalculateLoanPaymentRequest;
  refiCost: number;
}

export interface LoanComparisonResponse {
  currentPayment: MonthlyPaymentResponse;
  newPayment: MonthlyPaymentResponse;
  monthlySavings: number;
  totalSavings: number;
  breakEvenMonths: number;
}

export async function compareLoans(
  request: CompareLoansRequest
): Promise<LoanComparisonResponse> {
  return apiClient.post<LoanComparisonResponse>(
    `${CALCULATOR_ENDPOINT}/compare`,
    {
      current_loan: {
        principal: request.currentLoan.principal,
        rate: request.currentLoan.rate,
        term: request.currentLoan.term,
      },
      new_loan: {
        principal: request.newLoan.principal,
        rate: request.newLoan.rate,
        term: request.newLoan.term,
      },
      refi_cost: request.refiCost,
    }
  );
}

// Export all functions as a calculator API object
export const calculatorApi = {
  calculateMonthlyPayment,
  getAmortizationSchedule,
  calculateBreakEven,
  calculateRecoup,
  findTargetRate,
  compareLoans,
};

export default calculatorApi;
