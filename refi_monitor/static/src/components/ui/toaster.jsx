import { useToast } from './use-toast';
import { Toast, ToastClose, ToastDescription, ToastTitle } from './toast';

function Toaster() {
  const { toasts } = useToast();

  return (
    <div className="fixed bottom-0 right-0 z-50 flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:max-w-[420px]">
      {toasts.map(({ id, title, description, variant, open, ...props }) => {
        if (!open) return null;
        return (
          <Toast key={id} variant={variant} {...props}>
            <div className="grid gap-1">
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && (
                <ToastDescription>{description}</ToastDescription>
              )}
            </div>
            <ToastClose onClick={() => props.onOpenChange?.(false)} />
          </Toast>
        );
      })}
    </div>
  );
}

export { Toaster };
