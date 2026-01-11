export interface MortgageData {
  name: string;
  zipCode: string;
  originalPrincipal: number;
  originalTerm: number; // years
  originalInterestRate: number; // percentage (e.g., 6.5)
  remainingPrincipal: number;
  remainingTerm: number; // months
  creditScore: number;
}

export interface RefinanceData {
  targetTerm: number; // years
  targetMonthlyPayment?: number;
  targetInterestRate?: number; // percentage
  estimatedRefinanceCost: number;
}

export interface CalculatorFormData {
  mortgage: MortgageData;
  refinance: RefinanceData;
}

export interface FormFieldProps {
  id: string;
  label: string;
  type?: 'text' | 'number';
  value: string | number;
  onChange: (value: string) => void;
  error?: string;
  placeholder?: string;
  prefix?: string;
  suffix?: string;
  min?: number;
  max?: number;
  step?: number;
  required?: boolean;
  helpText?: string;
}

export interface FormErrors {
  [key: string]: string | undefined;
}
