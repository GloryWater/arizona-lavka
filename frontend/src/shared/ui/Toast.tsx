import { Toaster, toast } from 'sonner';
import React from 'react';
import { cn } from '@/shared/lib/utils';

// ============================================================================
// TOAST CONTAINER
// ============================================================================

interface ToastContainerProps {
  position?: 'top-right' | 'top-left' | 'top-center' | 'bottom-right' | 'bottom-left' | 'bottom-center';
  theme?: 'light' | 'dark' | 'system';
}

const ToastContainer: React.FC<ToastContainerProps> = ({
  position = 'top-right',
  theme = 'system',
}) => {
  const positionMap = {
    'top-right': 'top-right',
    'top-left': 'top-left',
    'top-center': 'top-center',
    'bottom-right': 'bottom-right',
    'bottom-left': 'bottom-left',
    'bottom-center': 'bottom-center',
  } as const;

  return (
    <Toaster
      position={positionMap[position]}
      theme={theme}
      toastOptions={{
        classNames: {
          toast: cn(
            'group toast',
            'group-[.toaster]:bg-card',
            'group-[.toaster]:text-foreground',
            'group-[.toaster]:border-border',
            'group-[.toaster]:shadow-lg',
            'group-[.toaster]:rounded-xl',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
          ),
          description: 'group-[.toast]:text-muted-foreground leading-relaxed',
          actionButton:
            'group-[.toast]:bg-primary group-[.toast]:text-primary-foreground group-[.toast]:rounded-lg group-[.toast]:px-4 group-[.toast]:py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          cancelButton:
            'group-[.toast]:bg-muted group-[.toast]:text-muted-foreground group-[.toast]:rounded-lg group-[.toast]:px-4 group-[.toast]:py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        },
      }}
      expand
      visibleToasts={5}
      duration={4000}
      closeButton
    />
  );
};

// ============================================================================
// TOAST HOOK
// ============================================================================

interface ToastOptions {
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  cancel?: {
    label: string;
    onClick: () => void;
  };
  onDismiss?: () => void;
}

const useToast = () => {
  const success = (message: string, title?: string, options?: ToastOptions) => {
    return toast.success(title || 'Успешно', {
      description: message,
      ...options,
    });
  };

  const error = (message: string, title?: string, options?: ToastOptions) => {
    return toast.error(title || 'Ошибка', {
      description: message,
      ...options,
    });
  };

  const warning = (message: string, title?: string, options?: ToastOptions) => {
    return toast.warning(title || 'Внимание', {
      description: message,
      ...options,
    });
  };

  const info = (message: string, title?: string, options?: ToastOptions) => {
    return toast.info(title || 'Информация', {
      description: message,
      ...options,
    });
  };

  const loading = (message: string, title?: string, options?: ToastOptions) => {
    return toast.loading(title || 'Загрузка', {
      description: message,
      ...options,
    });
  };

  const promise = <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string;
      error: string;
    },
    options?: ToastOptions
  ) => {
    return toast.promise(promise, {
      loading: messages.loading,
      success: messages.success,
      error: messages.error,
      ...options,
    });
  };

  const dismiss = (toastId: string | number) => {
    toast.dismiss(toastId);
  };

  return {
    success,
    error,
    warning,
    info,
    loading,
    promise,
    dismiss,
  };
};

export { ToastContainer, useToast };
