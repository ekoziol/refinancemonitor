import { useCallback, useEffect, useRef, useState } from 'react';
import { InputForm } from './InputForm';
import { SummaryTable } from './SummaryTable';
import { ErrorDisplay } from './ErrorDisplay';
import { LoadingSpinner } from './LoadingSpinner';
import { useCalculator } from '../hooks/useCalculator';
import type { CalculatorFormData } from '../types/forms';

export function CalculatorPage() {
  const [formData, setFormData] = useState<CalculatorFormData | null>(null);
  const lastCalculatedRef = useRef<string>('');

  const { results, isLoading, error, calculate, calculateImmediate, reset } = useCalculator({
    debounceMs: 500,
    onError: (err) => {
      console.error('Calculation error:', err);
    },
  });

  // Auto-calculate when form data changes (debounced)
  useEffect(() => {
    if (!formData) return;

    // Create a hash of the form data to check if it changed
    const dataHash = JSON.stringify(formData);
    if (dataHash === lastCalculatedRef.current) return;

    // Only auto-calculate if we have enough data
    const { mortgage, refinance } = formData;
    const hasRequiredData =
      mortgage.originalPrincipal > 0 &&
      mortgage.remainingPrincipal > 0 &&
      mortgage.originalInterestRate > 0 &&
      mortgage.remainingTerm > 0;

    if (hasRequiredData) {
      lastCalculatedRef.current = dataHash;
      calculate(formData);
    }
  }, [formData, calculate]);

  // Handle form data changes (for auto-calculation)
  const handleFormChange = useCallback((data: CalculatorFormData) => {
    setFormData(data);
  }, []);

  // Handle explicit calculate button click
  const handleSubmit = useCallback(
    async (data: CalculatorFormData) => {
      setFormData(data);
      lastCalculatedRef.current = JSON.stringify(data);
      calculateImmediate(data);
    },
    [calculateImmediate]
  );

  // Retry after error
  const handleRetry = useCallback(() => {
    if (formData) {
      calculateImmediate(formData);
    }
  }, [formData, calculateImmediate]);

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Refinance Calculator</h1>
          <p className="text-gray-600">
            Calculate your potential savings from refinancing your mortgage
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Input Form */}
          <div>
            <InputFormWithAutoCalc
              onSubmit={handleSubmit}
              onChange={handleFormChange}
              isLoading={isLoading}
            />
          </div>

          {/* Results Section */}
          <div className="space-y-4">
            {/* Loading indicator overlay for auto-calc */}
            {isLoading && results && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <LoadingSpinner size="sm" />
                <span>Updating...</span>
              </div>
            )}

            {/* Error Display */}
            <ErrorDisplay error={error} onRetry={handleRetry} />

            {/* Results Table */}
            <SummaryTable results={results} isLoading={isLoading && !results} />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Extended InputForm that reports changes for auto-calculation
 */
interface InputFormWithAutoCalcProps {
  onSubmit: (data: CalculatorFormData) => void | Promise<void>;
  onChange: (data: CalculatorFormData) => void;
  isLoading: boolean;
}

function InputFormWithAutoCalc({ onSubmit, onChange, isLoading }: InputFormWithAutoCalcProps) {
  const formDataRef = useRef<CalculatorFormData | null>(null);

  // Custom submit handler that captures form data
  const handleSubmit = useCallback(
    async (data: CalculatorFormData) => {
      formDataRef.current = data;
      onChange(data);
      await onSubmit(data);
    },
    [onSubmit, onChange]
  );

  return (
    <InputFormWrapper onSubmit={handleSubmit} onChange={onChange} isLoading={isLoading} />
  );
}

/**
 * InputForm wrapper that tracks changes and reports them
 */
interface InputFormWrapperProps {
  onSubmit: (data: CalculatorFormData) => void | Promise<void>;
  onChange: (data: CalculatorFormData) => void;
  isLoading: boolean;
}

function InputFormWrapper({ onSubmit, onChange, isLoading }: InputFormWrapperProps) {
  // We need to modify InputForm to support onChange for auto-calculation
  // For now, we'll just use the existing InputForm with the loading state

  return (
    <div className="relative">
      <InputForm onSubmit={onSubmit} />
      {isLoading && (
        <div className="absolute top-2 right-2">
          <LoadingSpinner size="sm" />
        </div>
      )}
    </div>
  );
}
