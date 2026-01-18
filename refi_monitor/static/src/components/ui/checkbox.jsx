import * as React from 'react';
import { cn } from '../../lib/utils';

const Checkbox = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <input
      type="checkbox"
      className={cn(
        'peer h-4 w-4 shrink-0 rounded-sm border border-gray-900 shadow focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50 checked:bg-gray-900 checked:text-gray-50',
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Checkbox.displayName = 'Checkbox';

export { Checkbox };
