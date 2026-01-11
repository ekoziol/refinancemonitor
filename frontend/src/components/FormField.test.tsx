import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormField } from './FormField';

describe('FormField', () => {
  const defaultProps = {
    id: 'test-field',
    label: 'Test Label',
    value: '',
    onChange: vi.fn(),
  };

  it('renders with label', () => {
    render(<FormField {...defaultProps} />);
    expect(screen.getByLabelText('Test Label')).toBeInTheDocument();
  });

  it('renders with correct id', () => {
    render(<FormField {...defaultProps} />);
    expect(screen.getByLabelText('Test Label')).toHaveAttribute('id', 'test-field');
  });

  it('displays current value', () => {
    render(<FormField {...defaultProps} value="test value" />);
    expect(screen.getByLabelText('Test Label')).toHaveValue('test value');
  });

  it('calls onChange when user types', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FormField {...defaultProps} onChange={onChange} />);

    await user.type(screen.getByLabelText('Test Label'), 'a');
    expect(onChange).toHaveBeenCalledWith('a');
  });

  it('renders as text input by default', () => {
    render(<FormField {...defaultProps} />);
    expect(screen.getByLabelText('Test Label')).toHaveAttribute('type', 'text');
  });

  it('renders as number input when specified', () => {
    render(<FormField {...defaultProps} type="number" />);
    expect(screen.getByLabelText('Test Label')).toHaveAttribute('type', 'number');
  });

  it('displays placeholder text', () => {
    render(<FormField {...defaultProps} placeholder="Enter value" />);
    expect(screen.getByLabelText('Test Label')).toHaveAttribute('placeholder', 'Enter value');
  });

  it('displays error message when provided', () => {
    render(<FormField {...defaultProps} error="This field is required" />);
    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });

  it('has error styling when error is present', () => {
    render(<FormField {...defaultProps} error="Error message" />);
    const input = screen.getByLabelText('Test Label');
    expect(input).toHaveClass('border-red-500');
  });

  it('displays prefix when provided', () => {
    render(<FormField {...defaultProps} prefix="$" />);
    expect(screen.getByText('$')).toBeInTheDocument();
  });

  it('displays suffix when provided', () => {
    render(<FormField {...defaultProps} suffix="%" />);
    expect(screen.getByText('%')).toBeInTheDocument();
  });

  it('respects min and max for number inputs', () => {
    render(<FormField {...defaultProps} type="number" min={0} max={100} />);
    const input = screen.getByLabelText('Test Label');
    expect(input).toHaveAttribute('min', '0');
    expect(input).toHaveAttribute('max', '100');
  });

  it('respects step for number inputs', () => {
    render(<FormField {...defaultProps} type="number" step={0.01} />);
    expect(screen.getByLabelText('Test Label')).toHaveAttribute('step', '0.01');
  });

  it('marks field as required when specified', () => {
    render(<FormField {...defaultProps} required />);
    expect(screen.getByRole('textbox')).toBeRequired();
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('displays help text when provided', () => {
    render(<FormField {...defaultProps} helpText="Enter your value here" />);
    expect(screen.getByText('Enter your value here')).toBeInTheDocument();
  });

  it('has proper ARIA attributes for accessibility', () => {
    render(<FormField {...defaultProps} error="Error" helpText="Help" />);
    const input = screen.getByLabelText('Test Label');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby');
  });

  it('renders numeric value correctly', () => {
    render(<FormField {...defaultProps} type="number" value={12345} />);
    expect(screen.getByLabelText('Test Label')).toHaveValue(12345);
  });
});
