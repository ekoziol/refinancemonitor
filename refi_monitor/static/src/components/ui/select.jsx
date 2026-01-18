import * as React from 'react';
import { cn } from '../../lib/utils';

const Select = React.forwardRef(({ className, children, ...props }, ref) => {
  return (
    <select
      className={cn(
        'flex h-9 w-full items-center justify-between whitespace-nowrap rounded-md border border-gray-200 bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      ref={ref}
      {...props}
    >
      {children}
    </select>
  );
});
Select.displayName = 'Select';

const SelectOption = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <option
      ref={ref}
      className={cn('relative flex w-full cursor-default select-none py-1.5 pl-2 pr-8 text-sm outline-none', className)}
      {...props}
    />
  );
});
SelectOption.displayName = 'SelectOption';

export { Select, SelectOption };
