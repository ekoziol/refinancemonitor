import * as React from 'react';
import { createPortal } from 'react-dom';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const SheetContext = React.createContext({
  open: false,
  onOpenChange: () => {},
  side: 'right',
});

const Sheet = ({ open, onOpenChange, children }) => {
  return (
    <SheetContext.Provider value={{ open, onOpenChange, side: 'right' }}>
      {children}
    </SheetContext.Provider>
  );
};

const SheetTrigger = React.forwardRef(
  ({ className, asChild, children, ...props }, ref) => {
    const { onOpenChange } = React.useContext(SheetContext);
    const handleClick = (e) => {
      props.onClick?.(e);
      onOpenChange(true);
    };

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        ...props,
        ref,
        onClick: handleClick,
      });
    }

    return (
      <button
        type="button"
        ref={ref}
        className={className}
        onClick={handleClick}
        {...props}
      >
        {children}
      </button>
    );
  }
);
SheetTrigger.displayName = 'SheetTrigger';

const SheetClose = React.forwardRef(
  ({ className, asChild, children, ...props }, ref) => {
    const { onOpenChange } = React.useContext(SheetContext);
    const handleClick = (e) => {
      props.onClick?.(e);
      onOpenChange(false);
    };

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        ...props,
        ref,
        onClick: handleClick,
      });
    }

    return (
      <button
        type="button"
        ref={ref}
        className={className}
        onClick={handleClick}
        {...props}
      >
        {children}
      </button>
    );
  }
);
SheetClose.displayName = 'SheetClose';

const SheetPortal = ({ children }) => {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  if (!mounted) return null;

  return createPortal(children, document.body);
};

const SheetOverlay = React.forwardRef(({ className, ...props }, ref) => {
  const { open, onOpenChange } = React.useContext(SheetContext);

  if (!open) return null;

  return (
    <div
      ref={ref}
      className={cn(
        'fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
        className
      )}
      onClick={() => onOpenChange(false)}
      data-state={open ? 'open' : 'closed'}
      {...props}
    />
  );
});
SheetOverlay.displayName = 'SheetOverlay';

const sheetVariants = cva(
  'fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out data-[state=closed]:duration-300 data-[state=open]:duration-500 data-[state=open]:animate-in data-[state=closed]:animate-out',
  {
    variants: {
      side: {
        top: 'inset-x-0 top-0 border-b border-border data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top',
        bottom:
          'inset-x-0 bottom-0 border-t border-border data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom',
        left: 'inset-y-0 left-0 h-full w-3/4 border-r border-border data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:max-w-sm',
        right:
          'inset-y-0 right-0 h-full w-3/4 border-l border-border data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-sm',
      },
    },
    defaultVariants: {
      side: 'right',
    },
  }
);

const SheetContent = React.forwardRef(
  ({ side = 'right', className, children, ...props }, ref) => {
    const { open, onOpenChange } = React.useContext(SheetContext);

    React.useEffect(() => {
      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          onOpenChange(false);
        }
      };

      if (open) {
        document.addEventListener('keydown', handleEscape);
        document.body.style.overflow = 'hidden';
      }

      return () => {
        document.removeEventListener('keydown', handleEscape);
        document.body.style.overflow = '';
      };
    }, [open, onOpenChange]);

    if (!open) return null;

    return (
      <SheetPortal>
        <SheetOverlay />
        <div
          ref={ref}
          className={cn(sheetVariants({ side }), className)}
          data-state={open ? 'open' : 'closed'}
          onClick={(e) => e.stopPropagation()}
          {...props}
        >
          <SheetClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none">
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
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
            <span className="sr-only">Close</span>
          </SheetClose>
          {children}
        </div>
      </SheetPortal>
    );
  }
);
SheetContent.displayName = 'SheetContent';

const SheetHeader = ({ className, ...props }) => (
  <div
    className={cn(
      'flex flex-col space-y-2 text-center sm:text-left',
      className
    )}
    {...props}
  />
);
SheetHeader.displayName = 'SheetHeader';

const SheetFooter = ({ className, ...props }) => (
  <div
    className={cn(
      'flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2',
      className
    )}
    {...props}
  />
);
SheetFooter.displayName = 'SheetFooter';

const SheetTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h2
    ref={ref}
    className={cn('text-lg font-semibold text-foreground', className)}
    {...props}
  />
));
SheetTitle.displayName = 'SheetTitle';

const SheetDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p ref={ref} className={cn('text-sm text-muted-foreground', className)} {...props} />
));
SheetDescription.displayName = 'SheetDescription';

export {
  Sheet,
  SheetPortal,
  SheetOverlay,
  SheetTrigger,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
};
