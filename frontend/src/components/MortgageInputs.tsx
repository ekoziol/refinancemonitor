import type { MortgageData, FormErrors } from '../types/forms';
import { FormField } from './FormField';

interface MortgageInputsProps {
  data: MortgageData;
  onChange: (field: keyof MortgageData, value: string) => void;
  errors: FormErrors;
}

export function MortgageInputs({ data, onChange, errors }: MortgageInputsProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Original Mortgage Details</h2>

      <FormField
        id="mortgage-name"
        label="Mortgage Name"
        value={data.name}
        onChange={(value) => onChange('name', value)}
        error={errors.name}
        placeholder="e.g., Primary Home"
        required
      />

      <FormField
        id="zip-code"
        label="Zip Code"
        value={data.zipCode}
        onChange={(value) => onChange('zipCode', value)}
        error={errors.zipCode}
        placeholder="12345"
        helpText="Enter your 5-digit zip code"
        required
      />

      <FormField
        id="original-principal"
        label="Original Principal"
        type="number"
        value={data.originalPrincipal || ''}
        onChange={(value) => onChange('originalPrincipal', value)}
        error={errors.originalPrincipal}
        prefix="$"
        min={0}
        step={1000}
        placeholder="300000"
        required
      />

      <FormField
        id="original-term"
        label="Original Term (Years)"
        type="number"
        value={data.originalTerm || ''}
        onChange={(value) => onChange('originalTerm', value)}
        error={errors.originalTerm}
        min={5}
        max={50}
        step={1}
        placeholder="30"
        required
      />

      <FormField
        id="original-interest-rate"
        label="Original Interest Rate"
        type="number"
        value={data.originalInterestRate || ''}
        onChange={(value) => onChange('originalInterestRate', value)}
        error={errors.originalInterestRate}
        suffix="%"
        min={0}
        max={100}
        step={0.125}
        placeholder="6.5"
        required
      />

      <FormField
        id="remaining-principal"
        label="Remaining Principal"
        type="number"
        value={data.remainingPrincipal || ''}
        onChange={(value) => onChange('remainingPrincipal', value)}
        error={errors.remainingPrincipal}
        prefix="$"
        min={0}
        step={1000}
        placeholder="250000"
        required
      />

      <FormField
        id="remaining-term"
        label="Remaining Term (Months)"
        type="number"
        value={data.remainingTerm || ''}
        onChange={(value) => onChange('remainingTerm', value)}
        error={errors.remainingTerm}
        min={1}
        max={600}
        step={1}
        placeholder="300"
        required
      />

      <FormField
        id="credit-score"
        label="Credit Score"
        type="number"
        value={data.creditScore || ''}
        onChange={(value) => onChange('creditScore', value)}
        error={errors.creditScore}
        min={300}
        max={850}
        step={1}
        placeholder="720"
        helpText="Score between 300-850"
        required
      />
    </div>
  );
}
