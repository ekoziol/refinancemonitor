import * as React from 'react';
import { cn } from '../../lib/utils';
import { Spinner } from './spinner';
import { Skeleton } from './skeleton';

/**
 * LoadingState - A component for displaying loading states with various styles.
 *
 * @param {string} variant - 'spinner' | 'skeleton' | 'overlay'
 * @param {string} size - 'sm' | 'default' | 'lg'
 * @param {string} message - Optional message to display
 * @param {number} skeletonCount - Number of skeleton rows (for skeleton variant)
 * @param {string} className - Additional CSS classes
 */
function LoadingState({
  variant = 'spinner',
  size = 'default',
  message,
  skeletonCount = 3,
  className,
  ...props
}) {
  if (variant === 'skeleton') {
    return (
      <div className={cn('space-y-3', className)} {...props}>
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <Skeleton
            key={i}
            className={cn(
              'w-full',
              size === 'sm' && 'h-4',
              size === 'default' && 'h-6',
              size === 'lg' && 'h-8'
            )}
          />
        ))}
      </div>
    );
  }

  if (variant === 'overlay') {
    return (
      <div
        className={cn(
          'absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-gray-900/80',
          className
        )}
        {...props}
      >
        <div className="flex flex-col items-center gap-2">
          <Spinner size={size} />
          {message && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{message}</p>
          )}
        </div>
      </div>
    );
  }

  // Default: spinner variant
  return (
    <div
      className={cn('flex flex-col items-center justify-center py-8', className)}
      {...props}
    >
      <Spinner size={size} />
      {message && (
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">{message}</p>
      )}
    </div>
  );
}

LoadingState.displayName = 'LoadingState';

export { LoadingState };
