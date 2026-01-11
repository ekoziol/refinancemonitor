import type { RefinanceData, FormErrors } from '../types/forms';
import { FormField } from './FormField';

interface RefinanceInputsProps {
  data: RefinanceData;
  onChange: (field: keyof RefinanceData, value: string) => void;
  errors: FormErrors;
}

export function RefinanceInputs({ data, onChange, errors }: RefinanceInputsProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Refinance Scenario</h2>

      <FormField
        id="target-term"
        label="Target Term (Years)"
        type="number"
        value={data.targetTerm || ''}
        onChange={(value) => onChange('targetTerm', value)}
        error={errors.targetTerm}
        min={5}
        max={50}
        step={1}
        placeholder="30"
        required
      />

      <FormField
        id="target-monthly-payment"
        label="Target Monthly Payment"
        type="number"
        value={data.targetMonthlyPayment || ''}
        onChange={(value) => onChange('targetMonthlyPayment', value)}
        error={errors.targetMonthlyPayment}
        prefix="$"
        min={0}
        step={50}
        placeholder="2000"
        helpText="Optional - leave blank to calculate"
      />

      <FormField
        id="target-interest-rate"
        label="Target Interest Rate"
        type="number"
        value={data.targetInterestRate || ''}
        onChange={(value) => onChange('targetInterestRate', value)}
        error={errors.targetInterestRate}
        suffix="%"
        min={0}
        max={100}
        step={0.125}
        placeholder="5.5"
        helpText="Optional - or use current market rate"
      />

      <FormField
        id="estimated-refinance-cost"
        label="Estimated Refinance Cost"
        type="number"
        value={data.estimatedRefinanceCost || ''}
        onChange={(value) => onChange('estimatedRefinanceCost', value)}
        error={errors.estimatedRefinanceCost}
        prefix="$"
        min={0}
        step={500}
        placeholder="5000"
        helpText="Closing costs, fees, etc."
        required
      />
    </div>
  );
}
