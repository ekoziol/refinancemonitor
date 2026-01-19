import * as React from 'react';
import { cn } from '../../lib/utils';
import { Button } from './button';

/**
 * ErrorState - A component for displaying error states with retry functionality.
 *
 * @param {string} title - Error title
 * @param {string} message - Error message or description
 * @param {Error} error - Error object (optional, extracts message if provided)
 * @param {function} onRetry - Callback function for retry action
 * @param {string} retryLabel - Label for retry button
 * @param {string} variant - 'default' | 'inline' | 'minimal'
 * @param {string} className - Additional CSS classes
 */
function ErrorState({
  title = 'Something went wrong',
  message,
  error,
  onRetry,
  retryLabel = 'Try again',
  variant = 'default',
  className,
  ...props
}) {
  const errorMessage = message || error?.message || 'An unexpected error occurred.';

  if (variant === 'minimal') {
    return (
      <div
        className={cn('flex items-center gap-2 text-sm text-red-600', className)}
        {...props}
      >
        <svg
          className="h-4 w-4 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span>{errorMessage}</span>
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-red-700 underline hover:text-red-800"
          >
            {retryLabel}
          </button>
        )}
      </div>
    );
  }

  if (variant === 'inline') {
    return (
      <div
        className={cn(
          'flex items-center justify-between rounded-md border border-red-200 bg-red-50 px-4 py-3',
          className
        )}
        {...props}
      >
        <div className="flex items-center gap-2">
          <svg
            className="h-5 w-5 text-red-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-sm text-red-700">{errorMessage}</p>
        </div>
        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="border-red-300 text-red-700 hover:bg-red-100"
          >
            {retryLabel}
          </Button>
        )}
      </div>
    );
  }

  // Default variant: centered block with icon
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 text-center',
        className
      )}
      {...props}
    >
      <div className="rounded-full bg-red-100 p-3">
        <svg
          className="h-6 w-6 text-red-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h3 className="mt-4 text-lg font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-gray-500">{errorMessage}</p>
      {onRetry && (
        <Button onClick={onRetry} className="mt-4" variant="outline">
          {retryLabel}
        </Button>
      )}
    </div>
  );
}

ErrorState.displayName = 'ErrorState';

export { ErrorState };
