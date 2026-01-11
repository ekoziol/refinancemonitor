/**
 * TypeScript types for refinance calculator API
 */

// Request types
export interface CalculateLoanPaymentRequest {
  principal: number;
  rate: number;
  term: number;
}

export interface CalculateBreakEvenRequest {
  originalPrincipal: number;
  originalRate: number;
  originalTerm: number;
  currentPrincipal: number;
  termRemaining: number;
  newTerm: number;
  refiCost: number;
}

export interface CalculateRecoupRequest {
  originalMonthlyPayment: number;
  refiMonthlyPayment: number;
  targetTerm: number;
  refiCost: number;
}

export interface FindTargetRateRequest {
  principal: number;
  term: number;
  targetPayment: number;
}

// Response types
export interface MonthlyPaymentResponse {
  monthlyPayment: number;
  totalPayment: number;
  totalInterest: number;
}

export interface AmortizationEntry {
  month: number;
  monthsRemaining: number;
  amountRemaining: number;
  principalPayment: number;
  interestPayment: number;
}

export interface AmortizationScheduleResponse {
  schedule: AmortizationEntry[];
  monthlyPayment: number;
  totalPayment: number;
  totalInterest: number;
}

export interface BreakEvenEntry {
  month: number;
  amountRemaining: number;
  interestRate: number;
  totalNewInterest: number;
  totalInterestPaid: number;
}

export interface BreakEvenAnalysisResponse {
  efficientFrontier: BreakEvenEntry[];
  breakEvenRate: number;
  potentialSavings: number;
}

export interface RecoupEntry {
  month: number;
  monthlySavings: number;
  cumulativeSavings: number;
}

export interface RecoupAnalysisResponse {
  schedule: RecoupEntry[];
  breakEvenMonth: number;
  totalSavings: number;
}

export interface TargetRateResponse {
  targetRate: number;
  monthlyPayment: number;
}

// Generic API response wrapper
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

// Calculator state for React components
export interface CalculatorState {
  principal: number;
  rate: number;
  term: number;
  refiCost: number;
  newTerm: number;
  targetPayment?: number;
}

export interface CalculatorResults {
  currentPayment: MonthlyPaymentResponse | null;
  newPayment: MonthlyPaymentResponse | null;
  breakEven: BreakEvenAnalysisResponse | null;
  recoup: RecoupAnalysisResponse | null;
}
