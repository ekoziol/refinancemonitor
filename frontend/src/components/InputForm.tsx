import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import type { MortgageData, RefinanceData, CalculatorFormData, FormErrors } from '../types/forms';
import { MortgageInputs } from './MortgageInputs';
import { RefinanceInputs } from './RefinanceInputs';

interface InputFormProps {
  onSubmit: (data: CalculatorFormData) => void | Promise<void>;
  onChange?: (data: CalculatorFormData) => void;
  initialData?: CalculatorFormData;
  isLoading?: boolean;
}

const defaultMortgageData: MortgageData = {
  name: '',
  zipCode: '',
  originalPrincipal: 0,
  originalTerm: 30,
  originalInterestRate: 0,
  remainingPrincipal: 0,
  remainingTerm: 0,
  creditScore: 0,
};

const defaultRefinanceData: RefinanceData = {
  targetTerm: 30,
  targetMonthlyPayment: undefined,
  targetInterestRate: undefined,
  estimatedRefinanceCost: 0,
};

function validateMortgage(data: MortgageData): FormErrors {
  const errors: FormErrors = {};

  if (!data.name) {
    errors.name = 'Mortgage name is required';
  }

  if (!data.zipCode) {
    errors.zipCode = 'Zip code is required';
  } else if (!/^\d{5}$/.test(data.zipCode)) {
    errors.zipCode = 'Zip code must be 5 digits';
  }

  if (!data.originalPrincipal || data.originalPrincipal <= 0) {
    errors.originalPrincipal = 'Original principal is required';
  }

  if (!data.originalTerm || data.originalTerm < 5 || data.originalTerm > 50) {
    errors.originalTerm = 'Term must be between 5 and 50 years';
  }

  if (!data.originalInterestRate || data.originalInterestRate <= 0) {
    errors.originalInterestRate = 'Interest rate is required';
  }

  if (!data.remainingPrincipal || data.remainingPrincipal <= 0) {
    errors.remainingPrincipal = 'Remaining principal is required';
  }

  if (!data.remainingTerm || data.remainingTerm <= 0) {
    errors.remainingTerm = 'Remaining term is required';
  }

  if (!data.creditScore || data.creditScore < 300 || data.creditScore > 850) {
    errors.creditScore = 'Credit score must be between 300 and 850';
  }

  return errors;
}

function validateRefinance(data: RefinanceData): FormErrors {
  const errors: FormErrors = {};

  if (!data.targetTerm || data.targetTerm < 5 || data.targetTerm > 50) {
    errors.targetTerm = 'Term must be between 5 and 50 years';
  }

  if (data.estimatedRefinanceCost === undefined || data.estimatedRefinanceCost < 0) {
    errors.estimatedRefinanceCost = 'Estimated refinance cost is required';
  }

  return errors;
}

export function InputForm({ onSubmit, onChange, initialData, isLoading }: InputFormProps) {
  const [mortgageData, setMortgageData] = useState<MortgageData>(
    initialData?.mortgage || defaultMortgageData
  );
  const [refinanceData, setRefinanceData] = useState<RefinanceData>(
    initialData?.refinance || defaultRefinanceData
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const isInitialMount = useRef(true);

  // Call onChange when form data changes (for auto-calculation)
  useEffect(() => {
    // Skip the initial mount to avoid calling onChange with default values
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    if (onChange) {
      onChange({
        mortgage: mortgageData,
        refinance: refinanceData,
      });
    }
  }, [mortgageData, refinanceData, onChange]);

  const handleMortgageChange = useCallback((field: keyof MortgageData, value: string) => {
    setMortgageData((prev) => {
      const numericFields: (keyof MortgageData)[] = [
        'originalPrincipal',
        'originalTerm',
        'originalInterestRate',
        'remainingPrincipal',
        'remainingTerm',
        'creditScore',
      ];

      const newValue = numericFields.includes(field) ? parseFloat(value) || 0 : value;

      return {
        ...prev,
        [field]: newValue,
      };
    });
    setTouched((prev) => new Set(prev).add(`mortgage.${field}`));
  }, []);

  const handleRefinanceChange = useCallback((field: keyof RefinanceData, value: string) => {
    setRefinanceData((prev) => {
      const numericFields: (keyof RefinanceData)[] = [
        'targetTerm',
        'targetMonthlyPayment',
        'targetInterestRate',
        'estimatedRefinanceCost',
      ];

      const newValue = numericFields.includes(field) ? parseFloat(value) || 0 : value;

      return {
        ...prev,
        [field]: newValue,
      };
    });
    setTouched((prev) => new Set(prev).add(`refinance.${field}`));
  }, []);

  // Validate on change, but only show errors for touched fields
  const displayedMortgageErrors = useMemo(() => {
    const allErrors = validateMortgage(mortgageData);
    const filtered: FormErrors = {};
    for (const [key, value] of Object.entries(allErrors)) {
      if (touched.has(`mortgage.${key}`)) {
        filtered[key] = value;
      }
    }
    return filtered;
  }, [mortgageData, touched]);

  const displayedRefinanceErrors = useMemo(() => {
    const allErrors = validateRefinance(refinanceData);
    const filtered: FormErrors = {};
    for (const [key, value] of Object.entries(allErrors)) {
      if (touched.has(`refinance.${key}`)) {
        filtered[key] = value;
      }
    }
    return filtered;
  }, [refinanceData, touched]);

  const isValid = useMemo(() => {
    const mortgageErrs = validateMortgage(mortgageData);
    const refinanceErrs = validateRefinance(refinanceData);
    return Object.keys(mortgageErrs).length === 0 && Object.keys(refinanceErrs).length === 0;
  }, [mortgageData, refinanceData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Mark all fields as touched
    const allFields = [
      ...Object.keys(mortgageData).map((k) => `mortgage.${k}`),
      ...Object.keys(refinanceData).map((k) => `refinance.${k}`),
    ];
    setTouched(new Set(allFields));

    // Validate - errors are already shown via displayedMortgageErrors/displayedRefinanceErrors
    const mortgageErrs = validateMortgage(mortgageData);
    const refinanceErrs = validateRefinance(refinanceData);

    if (Object.keys(mortgageErrs).length > 0 || Object.keys(refinanceErrs).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        mortgage: mortgageData,
        refinance: refinanceData,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      role="form"
      onSubmit={handleSubmit}
      className="space-y-6 max-w-2xl mx-auto p-6 bg-white rounded-lg shadow"
    >
      <MortgageInputs
        data={mortgageData}
        onChange={handleMortgageChange}
        errors={displayedMortgageErrors}
      />

      <div className="border-t border-gray-200 pt-6" />

      <RefinanceInputs
        data={refinanceData}
        onChange={handleRefinanceChange}
        errors={displayedRefinanceErrors}
      />

      <div className="pt-4">
        <button
          type="submit"
          disabled={!isValid || isSubmitting || isLoading}
          className={`w-full py-3 px-4 rounded-md font-medium text-white transition-colors ${
            isValid && !isSubmitting && !isLoading
              ? 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              : 'bg-gray-400 cursor-not-allowed'
          }`}
        >
          {isSubmitting || isLoading ? 'Calculating...' : 'Calculate Refinance Savings'}
        </button>
      </div>
    </form>
  );
}
