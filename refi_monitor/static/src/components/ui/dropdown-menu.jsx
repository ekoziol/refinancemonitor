import * as React from 'react';
import { cn } from '../../lib/utils';

const DropdownMenuContext = React.createContext({
  open: false,
  onOpenChange: () => {},
});

const DropdownMenu = ({ open: controlledOpen, onOpenChange, children }) => {
  const [uncontrolledOpen, setUncontrolledOpen] = React.useState(false);
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : uncontrolledOpen;

  const handleOpenChange = React.useCallback(
    (newOpen) => {
      if (!isControlled) {
        setUncontrolledOpen(newOpen);
      }
      onOpenChange?.(newOpen);
    },
    [isControlled, onOpenChange]
  );

  return (
    <DropdownMenuContext.Provider value={{ open, onOpenChange: handleOpenChange }}>
      <div className="relative inline-block text-left">{children}</div>
    </DropdownMenuContext.Provider>
  );
};

const DropdownMenuTrigger = React.forwardRef(
  ({ className, asChild, children, ...props }, ref) => {
    const { open, onOpenChange } = React.useContext(DropdownMenuContext);

    const handleClick = (e) => {
      e.stopPropagation();
      props.onClick?.(e);
      onOpenChange(!open);
    };

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        ...props,
        ref,
        onClick: handleClick,
        'aria-expanded': open,
        'aria-haspopup': 'menu',
      });
    }

    return (
      <button
        type="button"
        ref={ref}
        className={className}
        onClick={handleClick}
        aria-expanded={open}
        aria-haspopup="menu"
        {...props}
      >
        {children}
      </button>
    );
  }
);
DropdownMenuTrigger.displayName = 'DropdownMenuTrigger';

const DropdownMenuContent = React.forwardRef(
  ({ className, align = 'center', sideOffset = 4, children, ...props }, ref) => {
    const { open, onOpenChange } = React.useContext(DropdownMenuContext);
    const contentRef = React.useRef(null);

    React.useEffect(() => {
      const handleClickOutside = (e) => {
        if (contentRef.current && !contentRef.current.contains(e.target)) {
          onOpenChange(false);
        }
      };

      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          onOpenChange(false);
        }
      };

      if (open) {
        document.addEventListener('mousedown', handleClickOutside);
        document.addEventListener('keydown', handleEscape);
      }

      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleEscape);
      };
    }, [open, onOpenChange]);

    if (!open) return null;

    const alignClasses = {
      start: 'left-0',
      center: 'left-1/2 -translate-x-1/2',
      end: 'right-0',
    };

    return (
      <div
        ref={(node) => {
          contentRef.current = node;
          if (typeof ref === 'function') ref(node);
          else if (ref) ref.current = node;
        }}
        className={cn(
          'absolute z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white p-1 text-gray-950 shadow-md',
          'animate-in fade-in-0 zoom-in-95',
          alignClasses[align],
          className
        )}
        style={{ marginTop: sideOffset }}
        role="menu"
        {...props}
      >
        {children}
      </div>
    );
  }
);
DropdownMenuContent.displayName = 'DropdownMenuContent';

const DropdownMenuItem = React.forwardRef(
  ({ className, inset, onSelect, disabled, children, ...props }, ref) => {
    const { onOpenChange } = React.useContext(DropdownMenuContext);

    const handleClick = (e) => {
      if (disabled) {
        e.preventDefault();
        return;
      }
      props.onClick?.(e);
      onSelect?.(e);
      onOpenChange(false);
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-gray-100 focus:text-gray-900 hover:bg-gray-100 hover:text-gray-900',
          inset && 'pl-8',
          disabled && 'pointer-events-none opacity-50',
          className
        )}
        role="menuitem"
        onClick={handleClick}
        {...props}
      >
        {children}
      </div>
    );
  }
);
DropdownMenuItem.displayName = 'DropdownMenuItem';

const DropdownMenuCheckboxItem = React.forwardRef(
  ({ className, children, checked, onCheckedChange, ...props }, ref) => {
    const { onOpenChange } = React.useContext(DropdownMenuContext);

    const handleClick = (e) => {
      props.onClick?.(e);
      onCheckedChange?.(!checked);
      onOpenChange(false);
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-gray-100 focus:text-gray-900 hover:bg-gray-100 hover:text-gray-900',
          className
        )}
        role="menuitemcheckbox"
        aria-checked={checked}
        onClick={handleClick}
        {...props}
      >
        <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
          {checked && (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
            >
              <path d="M20 6 9 17l-5-5" />
            </svg>
          )}
        </span>
        {children}
      </div>
    );
  }
);
DropdownMenuCheckboxItem.displayName = 'DropdownMenuCheckboxItem';

const DropdownMenuRadioGroup = ({ value, onValueChange, children }) => {
  return (
    <div role="group">
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { currentValue: value, onValueChange });
        }
        return child;
      })}
    </div>
  );
};

const DropdownMenuRadioItem = React.forwardRef(
  ({ className, children, value, currentValue, onValueChange, ...props }, ref) => {
    const { onOpenChange } = React.useContext(DropdownMenuContext);
    const checked = value === currentValue;

    const handleClick = (e) => {
      props.onClick?.(e);
      onValueChange?.(value);
      onOpenChange(false);
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-gray-100 focus:text-gray-900 hover:bg-gray-100 hover:text-gray-900',
          className
        )}
        role="menuitemradio"
        aria-checked={checked}
        onClick={handleClick}
        {...props}
      >
        <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
          {checked && (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
            >
              <circle cx="12" cy="12" r="4" fill="currentColor" />
            </svg>
          )}
        </span>
        {children}
      </div>
    );
  }
);
DropdownMenuRadioItem.displayName = 'DropdownMenuRadioItem';

const DropdownMenuLabel = React.forwardRef(
  ({ className, inset, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'px-2 py-1.5 text-sm font-semibold',
        inset && 'pl-8',
        className
      )}
      {...props}
    />
  )
);
DropdownMenuLabel.displayName = 'DropdownMenuLabel';

const DropdownMenuSeparator = React.forwardRef(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('-mx-1 my-1 h-px bg-gray-100', className)}
      role="separator"
      {...props}
    />
  )
);
DropdownMenuSeparator.displayName = 'DropdownMenuSeparator';

const DropdownMenuShortcut = ({ className, ...props }) => {
  return (
    <span
      className={cn('ml-auto text-xs tracking-widest opacity-60', className)}
      {...props}
    />
  );
};
DropdownMenuShortcut.displayName = 'DropdownMenuShortcut';

const DropdownMenuGroup = ({ children, ...props }) => (
  <div role="group" {...props}>
    {children}
  </div>
);

const DropdownMenuSub = ({ children }) => {
  const [open, setOpen] = React.useState(false);
  return (
    <DropdownMenuContext.Provider value={{ open, onOpenChange: setOpen }}>
      <div className="relative">{children}</div>
    </DropdownMenuContext.Provider>
  );
};

const DropdownMenuSubTrigger = React.forwardRef(
  ({ className, inset, children, ...props }, ref) => {
    const { onOpenChange } = React.useContext(DropdownMenuContext);

    return (
      <div
        ref={ref}
        className={cn(
          'flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-gray-100 hover:bg-gray-100',
          inset && 'pl-8',
          className
        )}
        onMouseEnter={() => onOpenChange(true)}
        onMouseLeave={() => onOpenChange(false)}
        {...props}
      >
        {children}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="ml-auto h-4 w-4"
        >
          <path d="m9 18 6-6-6-6" />
        </svg>
      </div>
    );
  }
);
DropdownMenuSubTrigger.displayName = 'DropdownMenuSubTrigger';

const DropdownMenuSubContent = React.forwardRef(
  ({ className, ...props }, ref) => {
    const { open } = React.useContext(DropdownMenuContext);

    if (!open) return null;

    return (
      <div
        ref={ref}
        className={cn(
          'absolute left-full top-0 z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white p-1 text-gray-950 shadow-lg',
          'animate-in fade-in-0 zoom-in-95',
          className
        )}
        {...props}
      />
    );
  }
);
DropdownMenuSubContent.displayName = 'DropdownMenuSubContent';

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
};
