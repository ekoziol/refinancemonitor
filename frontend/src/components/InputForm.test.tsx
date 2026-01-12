import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InputForm } from './InputForm';
import type { CalculatorFormData } from '../types/forms';

describe('InputForm', () => {
  const defaultOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders both mortgage and refinance sections', () => {
    render(<InputForm onSubmit={defaultOnSubmit} />);
    expect(screen.getByRole('heading', { name: /original mortgage/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /refinance.*scenario/i })).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(<InputForm onSubmit={defaultOnSubmit} />);
    expect(screen.getByRole('button', { name: /calculate/i })).toBeInTheDocument();
  });

  it('submit button is disabled when form is invalid', () => {
    render(<InputForm onSubmit={defaultOnSubmit} />);
    expect(screen.getByRole('button', { name: /calculate/i })).toBeDisabled();
  });

  it('shows validation error for invalid zip code', async () => {
    const user = userEvent.setup();
    render(<InputForm onSubmit={defaultOnSubmit} />);

    const zipInput = screen.getByLabelText(/zip code/i);
    await user.type(zipInput, '123');
    await user.tab(); // blur to trigger validation

    await waitFor(() => {
      expect(screen.getByText(/5 digits/i)).toBeInTheDocument();
    });
  });

  it('shows validation error for credit score out of range', async () => {
    const user = userEvent.setup();
    render(<InputForm onSubmit={defaultOnSubmit} />);

    const creditInput = screen.getByLabelText(/credit score/i);
    await user.type(creditInput, '200');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/300.*850/i);
    });
  });

  it('enables submit when all required fields are filled', async () => {
    const user = userEvent.setup();
    render(<InputForm onSubmit={defaultOnSubmit} />);

    // Fill in all required fields (clear first to avoid appending to defaults)
    await user.type(screen.getByLabelText(/mortgage name/i), 'Home');
    await user.type(screen.getByLabelText(/zip code/i), '12345');
    await user.type(screen.getByLabelText(/original.*principal/i), '300000');
    await user.clear(screen.getByLabelText(/original.*term/i));
    await user.type(screen.getByLabelText(/original.*term/i), '30');
    await user.type(screen.getByLabelText(/original.*interest rate/i), '6.5');
    await user.type(screen.getByLabelText(/remaining.*principal/i), '250000');
    await user.type(screen.getByLabelText(/remaining.*term/i), '300');
    await user.type(screen.getByLabelText(/credit score/i), '720');
    await user.clear(screen.getByLabelText(/target.*term/i));
    await user.type(screen.getByLabelText(/target.*term/i), '30');
    await user.type(screen.getByLabelText(/estimated.*refinance.*cost/i), '5000');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /calculate/i })).toBeEnabled();
    });
  });

  it('calls onSubmit with form data when submitted', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<InputForm onSubmit={onSubmit} />);

    // Fill in all required fields (clear fields with defaults first)
    await user.type(screen.getByLabelText(/mortgage name/i), 'Home');
    await user.type(screen.getByLabelText(/zip code/i), '12345');
    await user.type(screen.getByLabelText(/original.*principal/i), '300000');
    await user.clear(screen.getByLabelText(/original.*term/i));
    await user.type(screen.getByLabelText(/original.*term/i), '30');
    await user.type(screen.getByLabelText(/original.*interest rate/i), '6.5');
    await user.type(screen.getByLabelText(/remaining.*principal/i), '250000');
    await user.type(screen.getByLabelText(/remaining.*term/i), '300');
    await user.type(screen.getByLabelText(/credit score/i), '720');
    await user.clear(screen.getByLabelText(/target.*term/i));
    await user.type(screen.getByLabelText(/target.*term/i), '30');
    await user.type(screen.getByLabelText(/estimated.*refinance.*cost/i), '5000');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /calculate/i })).toBeEnabled();
    });

    await user.click(screen.getByRole('button', { name: /calculate/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled();
    });

    const submittedData: CalculatorFormData = onSubmit.mock.calls[0][0];
    expect(submittedData.mortgage.name).toBe('Home');
    expect(submittedData.mortgage.zipCode).toBe('12345');
    expect(submittedData.mortgage.originalPrincipal).toBe(300000);
    expect(submittedData.refinance.estimatedRefinanceCost).toBe(5000);
  });

  it('prevents submission when form is invalid', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<InputForm onSubmit={onSubmit} />);

    // Only fill some fields
    await user.type(screen.getByLabelText(/mortgage name/i), 'Home');

    // Button should be disabled
    expect(screen.getByRole('button', { name: /calculate/i })).toBeDisabled();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('has responsive layout classes', () => {
    render(<InputForm onSubmit={defaultOnSubmit} />);
    const form = screen.getByRole('form');
    expect(form).toHaveClass('space-y-6');
  });

  it('displays loading state during submission', async () => {
    const onSubmit = vi.fn().mockImplementation(() => new Promise(() => {}));
    const user = userEvent.setup();
    render(<InputForm onSubmit={onSubmit} />);

    // Fill form (clear fields with defaults first)
    await user.type(screen.getByLabelText(/mortgage name/i), 'Home');
    await user.type(screen.getByLabelText(/zip code/i), '12345');
    await user.type(screen.getByLabelText(/original.*principal/i), '300000');
    await user.clear(screen.getByLabelText(/original.*term/i));
    await user.type(screen.getByLabelText(/original.*term/i), '30');
    await user.type(screen.getByLabelText(/original.*interest rate/i), '6.5');
    await user.type(screen.getByLabelText(/remaining.*principal/i), '250000');
    await user.type(screen.getByLabelText(/remaining.*term/i), '300');
    await user.type(screen.getByLabelText(/credit score/i), '720');
    await user.clear(screen.getByLabelText(/target.*term/i));
    await user.type(screen.getByLabelText(/target.*term/i), '30');
    await user.type(screen.getByLabelText(/estimated.*refinance.*cost/i), '5000');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /calculate/i })).toBeEnabled();
    });

    await user.click(screen.getByRole('button', { name: /calculate/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /calculating/i })).toBeInTheDocument();
    });
  });

  it('accepts initial values', () => {
    const initialData: CalculatorFormData = {
      mortgage: {
        name: 'My Home',
        zipCode: '90210',
        originalPrincipal: 500000,
        originalTerm: 30,
        originalInterestRate: 7.0,
        remainingPrincipal: 400000,
        remainingTerm: 300,
        creditScore: 750,
      },
      refinance: {
        targetTerm: 15,
        targetMonthlyPayment: undefined,
        targetInterestRate: undefined,
        estimatedRefinanceCost: 8000,
      },
    };

    render(<InputForm onSubmit={defaultOnSubmit} initialData={initialData} />);

    expect(screen.getByLabelText(/mortgage name/i)).toHaveValue('My Home');
    expect(screen.getByLabelText(/zip code/i)).toHaveValue('90210');
  });
});
