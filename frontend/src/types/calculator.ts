/**
 * Calculator API request and response types
 */

export interface CalculatorRequest {
  mortgage: {
    originalPrincipal: number;
    originalTerm: number; // years
    originalInterestRate: number; // percentage (e.g., 4.5 for 4.5%)
    remainingPrincipal: number;
    remainingTerm: number; // months
  };
  refinance: {
    targetTerm: number; // years
    targetMonthlyPayment?: number;
    targetInterestRate?: number; // percentage
    estimatedRefinanceCost: number;
  };
}

export interface CalculatorResponse {
  originalMonthlyPayment: number;
  minimumMonthlyPayment: number;
  refiMonthlyPayment: number;
  monthlySavings: number;
  targetInterestRate: number; // percentage
  originalInterest: number;
  refiInterest: number;
  totalLoanSavings: number;
  monthsToBreakevenSimple: number | null;
  monthsToBreakevenInterest: number | null;
  additionalMonths: number;
  cashRequired: number;
}

export interface CalculatorError {
  error: string;
}
