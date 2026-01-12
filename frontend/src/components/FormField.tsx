import type { FormFieldProps } from '../types/forms';

export function FormField({
  id,
  label,
  type = 'text',
  value,
  onChange,
  error,
  placeholder,
  prefix,
  suffix,
  min,
  max,
  step,
  required,
  helpText,
}: FormFieldProps) {
  const hasError = !!error;
  const describedBy = [
    error ? `${id}-error` : null,
    helpText ? `${id}-help` : null,
  ]
    .filter(Boolean)
    .join(' ');

  const inputClasses = [
    'block w-full rounded-md shadow-sm sm:text-sm',
    hasError
      ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
    prefix ? 'pl-7' : '',
    suffix ? 'pr-8' : '',
  ].join(' ');

  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <div className="relative">
        {prefix && (
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <span className="text-gray-500 sm:text-sm">{prefix}</span>
          </div>
        )}
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          min={min}
          max={max}
          step={step}
          required={required}
          aria-invalid={hasError}
          aria-describedby={describedBy || undefined}
          className={inputClasses}
        />
        {suffix && (
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <span className="text-gray-500 sm:text-sm">{suffix}</span>
          </div>
        )}
      </div>
      {helpText && (
        <p id={`${id}-help`} className="mt-1 text-sm text-gray-500">
          {helpText}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="mt-1 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
