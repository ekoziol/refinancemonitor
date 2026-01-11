import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MortgageInputs } from './MortgageInputs';
import type { MortgageData } from '../types/forms';

describe('MortgageInputs', () => {
  const defaultData: MortgageData = {
    name: '',
    zipCode: '',
    originalPrincipal: 0,
    originalTerm: 30,
    originalInterestRate: 0,
    remainingPrincipal: 0,
    remainingTerm: 0,
    creditScore: 0,
  };

  const defaultProps = {
    data: defaultData,
    onChange: vi.fn(),
    errors: {},
  };

  it('renders mortgage name field', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByLabelText(/mortgage name/i)).toBeInTheDocument();
  });

  it('renders zip code field', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByLabelText(/zip code/i)).toBeInTheDocument();
  });

  it('renders original principal field with currency prefix', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByLabelText(/original.*principal/i)).toBeInTheDocument();
    // Multiple $ symbols exist (for original and remaining principal)
    expect(screen.getAllByText('$').length).toBeGreaterThanOrEqual(1);
  });

  it('renders original term field in years', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByLabelText(/original.*term/i)).toBeInTheDocument();
  });

  it('renders original interest rate field with percentage suffix', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByLabelText(/original.*interest rate/i)).toBeInTheDocument();
    expect(screen.getByText('%')).toBeInTheDocument();
  });

  it('renders remaining principal field', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByLabelText(/remaining.*principal/i)).toBeInTheDocument();
  });

  it('renders remaining term field in months', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByLabelText(/remaining.*term/i)).toBeInTheDocument();
  });

  it('renders credit score field', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByLabelText(/credit score/i)).toBeInTheDocument();
  });

  it('displays current values', () => {
    const data: MortgageData = {
      name: 'Home Mortgage',
      zipCode: '12345',
      originalPrincipal: 300000,
      originalTerm: 30,
      originalInterestRate: 6.5,
      remainingPrincipal: 250000,
      remainingTerm: 300,
      creditScore: 720,
    };
    render(<MortgageInputs {...defaultProps} data={data} />);

    expect(screen.getByLabelText(/mortgage name/i)).toHaveValue('Home Mortgage');
    expect(screen.getByLabelText(/zip code/i)).toHaveValue('12345');
  });

  it('calls onChange when mortgage name is updated', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<MortgageInputs {...defaultProps} onChange={onChange} />);

    await user.type(screen.getByLabelText(/mortgage name/i), 'My Mortgage');
    expect(onChange).toHaveBeenCalled();
  });

  it('calls onChange with field name and value', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<MortgageInputs {...defaultProps} onChange={onChange} />);

    await user.type(screen.getByLabelText(/mortgage name/i), 'T');
    expect(onChange).toHaveBeenCalledWith('name', 'T');
  });

  it('displays error for invalid field', () => {
    const errors = { zipCode: 'Zip code must be 5 digits' };
    render(<MortgageInputs {...defaultProps} errors={errors} />);
    expect(screen.getByText('Zip code must be 5 digits')).toBeInTheDocument();
  });

  it('has proper section heading', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByRole('heading', { name: /original mortgage/i })).toBeInTheDocument();
  });

  it('all required fields are marked as required', () => {
    render(<MortgageInputs {...defaultProps} />);
    // Check that required indicator (*) appears for each required field
    const asterisks = screen.getAllByText('*');
    expect(asterisks.length).toBeGreaterThanOrEqual(7); // All fields except name are required
  });

  it('credit score has min and max constraints', () => {
    render(<MortgageInputs {...defaultProps} />);
    const creditScoreInput = screen.getByLabelText(/credit score/i);
    expect(creditScoreInput).toHaveAttribute('min', '300');
    expect(creditScoreInput).toHaveAttribute('max', '850');
  });

  it('zip code has proper validation pattern hint', () => {
    render(<MortgageInputs {...defaultProps} />);
    expect(screen.getByText(/5-digit zip code/i)).toBeInTheDocument();
  });
});
