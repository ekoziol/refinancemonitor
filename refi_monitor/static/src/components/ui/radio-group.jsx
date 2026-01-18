import * as React from 'react';
import { cn } from '../../lib/utils';

const RadioGroupContext = React.createContext(null);

const RadioGroup = React.forwardRef(
  ({ className, value, onValueChange, name, ...props }, ref) => {
    return (
      <RadioGroupContext.Provider value={{ value, onValueChange, name }}>
        <div
          ref={ref}
          className={cn('grid gap-2', className)}
          role="radiogroup"
          {...props}
        />
      </RadioGroupContext.Provider>
    );
  }
);
RadioGroup.displayName = 'RadioGroup';

const RadioGroupItem = React.forwardRef(
  ({ className, value: itemValue, id, ...props }, ref) => {
    const context = React.useContext(RadioGroupContext);
    const isChecked = context?.value === itemValue;

    const handleChange = () => {
      context?.onValueChange?.(itemValue);
    };

    return (
      <input
        type="radio"
        ref={ref}
        id={id}
        name={context?.name}
        value={itemValue}
        checked={isChecked}
        onChange={handleChange}
        className={cn(
          'aspect-square h-4 w-4 rounded-full border border-gray-900 text-gray-900 shadow focus:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        {...props}
      />
    );
  }
);
RadioGroupItem.displayName = 'RadioGroupItem';

export { RadioGroup, RadioGroupItem };
