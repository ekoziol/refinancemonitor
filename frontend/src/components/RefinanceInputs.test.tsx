import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RefinanceInputs } from './RefinanceInputs';
import type { RefinanceData } from '../types/forms';

describe('RefinanceInputs', () => {
  const defaultData: RefinanceData = {
    targetTerm: 30,
    targetMonthlyPayment: undefined,
    targetInterestRate: undefined,
    estimatedRefinanceCost: 0,
  };

  const defaultProps = {
    data: defaultData,
    onChange: vi.fn(),
    errors: {},
  };

  it('renders section heading', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getByRole('heading', { name: /refinance.*scenario/i })).toBeInTheDocument();
  });

  it('renders target term field', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getByLabelText(/target.*term/i)).toBeInTheDocument();
  });

  it('renders target monthly payment field', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getByLabelText(/target.*monthly.*payment/i)).toBeInTheDocument();
  });

  it('renders target interest rate field', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getByLabelText(/target.*interest.*rate/i)).toBeInTheDocument();
  });

  it('renders estimated refinance cost field', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getByLabelText(/estimated.*refinance.*cost/i)).toBeInTheDocument();
  });

  it('target term has year constraints', () => {
    render(<RefinanceInputs {...defaultProps} />);
    const termInput = screen.getByLabelText(/target.*term/i);
    expect(termInput).toHaveAttribute('min', '5');
    expect(termInput).toHaveAttribute('max', '50');
  });

  it('displays current values', () => {
    const data: RefinanceData = {
      targetTerm: 15,
      targetMonthlyPayment: 2000,
      targetInterestRate: 5.5,
      estimatedRefinanceCost: 5000,
    };
    render(<RefinanceInputs {...defaultProps} data={data} />);

    expect(screen.getByLabelText(/target.*term/i)).toHaveValue(15);
  });

  it('calls onChange when target term is updated', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<RefinanceInputs {...defaultProps} onChange={onChange} />);

    const termInput = screen.getByLabelText(/target.*term/i);
    await user.clear(termInput);
    await user.type(termInput, '15');
    expect(onChange).toHaveBeenCalled();
  });

  it('displays error for invalid field', () => {
    const errors = { targetTerm: 'Please enter a valid term' };
    render(<RefinanceInputs {...defaultProps} errors={errors} />);
    expect(screen.getByText('Please enter a valid term')).toBeInTheDocument();
  });

  it('target interest rate shows percentage suffix', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getByText('%')).toBeInTheDocument();
  });

  it('estimated refinance cost shows currency prefix', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getAllByText('$').length).toBeGreaterThanOrEqual(1);
  });

  it('target monthly payment is optional', () => {
    render(<RefinanceInputs {...defaultProps} />);
    const paymentInput = screen.getByLabelText(/target.*monthly.*payment/i);
    expect(paymentInput).not.toBeRequired();
  });

  it('target interest rate is optional', () => {
    render(<RefinanceInputs {...defaultProps} />);
    const rateInput = screen.getByLabelText(/target.*interest.*rate/i);
    expect(rateInput).not.toBeRequired();
  });

  it('estimated refinance cost is required', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getByRole('spinbutton', { name: /estimated.*refinance.*cost/i })).toBeRequired();
  });

  it('target term is required', () => {
    render(<RefinanceInputs {...defaultProps} />);
    expect(screen.getByRole('spinbutton', { name: /target.*term/i })).toBeRequired();
  });

  it('shows help text for optional fields', () => {
    render(<RefinanceInputs {...defaultProps} />);
    // Both target payment and target rate have "optional" help text
    expect(screen.getAllByText(/optional/i).length).toBe(2);
  });
});
