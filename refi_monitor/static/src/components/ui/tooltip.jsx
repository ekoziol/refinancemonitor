import * as React from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../../lib/utils';

const TooltipContext = React.createContext({
  open: false,
  onOpenChange: () => {},
});

const TooltipProvider = ({ children, delayDuration = 200 }) => {
  return <>{children}</>;
};

const Tooltip = ({ open: controlledOpen, onOpenChange, delayDuration = 200, children }) => {
  const [uncontrolledOpen, setUncontrolledOpen] = React.useState(false);
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : uncontrolledOpen;
  const timeoutRef = React.useRef(null);

  const handleOpenChange = React.useCallback(
    (newOpen) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      if (newOpen) {
        timeoutRef.current = setTimeout(() => {
          if (!isControlled) {
            setUncontrolledOpen(true);
          }
          onOpenChange?.(true);
        }, delayDuration);
      } else {
        if (!isControlled) {
          setUncontrolledOpen(false);
        }
        onOpenChange?.(false);
      }
    },
    [isControlled, onOpenChange, delayDuration]
  );

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <TooltipContext.Provider value={{ open, onOpenChange: handleOpenChange }}>
      {children}
    </TooltipContext.Provider>
  );
};

const TooltipTrigger = React.forwardRef(
  ({ className, asChild, children, ...props }, ref) => {
    const { onOpenChange } = React.useContext(TooltipContext);
    const [triggerRef, setTriggerRef] = React.useState(null);

    const handleMouseEnter = (e) => {
      props.onMouseEnter?.(e);
      onOpenChange(true);
    };

    const handleMouseLeave = (e) => {
      props.onMouseLeave?.(e);
      onOpenChange(false);
    };

    const handleFocus = (e) => {
      props.onFocus?.(e);
      onOpenChange(true);
    };

    const handleBlur = (e) => {
      props.onBlur?.(e);
      onOpenChange(false);
    };

    const combinedRef = React.useCallback(
      (node) => {
        setTriggerRef(node);
        if (typeof ref === 'function') {
          ref(node);
        } else if (ref) {
          ref.current = node;
        }
      },
      [ref]
    );

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        ...props,
        ref: combinedRef,
        onMouseEnter: handleMouseEnter,
        onMouseLeave: handleMouseLeave,
        onFocus: handleFocus,
        onBlur: handleBlur,
        'data-tooltip-trigger': true,
      });
    }

    return (
      <span
        ref={combinedRef}
        className={className}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
        data-tooltip-trigger
        {...props}
      >
        {children}
      </span>
    );
  }
);
TooltipTrigger.displayName = 'TooltipTrigger';

const TooltipPortal = ({ children }) => {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  if (!mounted) return null;

  return createPortal(children, document.body);
};

const TooltipContent = React.forwardRef(
  ({ className, sideOffset = 4, side = 'top', children, ...props }, ref) => {
    const { open } = React.useContext(TooltipContext);
    const [position, setPosition] = React.useState({ top: 0, left: 0 });
    const contentRef = React.useRef(null);

    React.useEffect(() => {
      if (open) {
        const trigger = document.querySelector('[data-tooltip-trigger]');
        if (trigger && contentRef.current) {
          const triggerRect = trigger.getBoundingClientRect();
          const contentRect = contentRef.current.getBoundingClientRect();

          let top, left;

          switch (side) {
            case 'top':
              top = triggerRect.top - contentRect.height - sideOffset;
              left = triggerRect.left + (triggerRect.width - contentRect.width) / 2;
              break;
            case 'bottom':
              top = triggerRect.bottom + sideOffset;
              left = triggerRect.left + (triggerRect.width - contentRect.width) / 2;
              break;
            case 'left':
              top = triggerRect.top + (triggerRect.height - contentRect.height) / 2;
              left = triggerRect.left - contentRect.width - sideOffset;
              break;
            case 'right':
              top = triggerRect.top + (triggerRect.height - contentRect.height) / 2;
              left = triggerRect.right + sideOffset;
              break;
            default:
              top = triggerRect.top - contentRect.height - sideOffset;
              left = triggerRect.left + (triggerRect.width - contentRect.width) / 2;
          }

          setPosition({ top: top + window.scrollY, left: left + window.scrollX });
        }
      }
    }, [open, side, sideOffset]);

    if (!open) return null;

    return (
      <TooltipPortal>
        <div
          ref={(node) => {
            contentRef.current = node;
            if (typeof ref === 'function') {
              ref(node);
            } else if (ref) {
              ref.current = node;
            }
          }}
          className={cn(
            'z-50 overflow-hidden rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground animate-in fade-in-0 zoom-in-95',
            className
          )}
          style={{
            position: 'absolute',
            top: position.top,
            left: position.left,
          }}
          {...props}
        >
          {children}
        </div>
      </TooltipPortal>
    );
  }
);
TooltipContent.displayName = 'TooltipContent';

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };
