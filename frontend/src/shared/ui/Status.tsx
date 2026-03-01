import React from 'react';
import { cn } from '@/shared/lib/utils';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle, XCircle, Info } from 'lucide-react';

// ============================================================================
// EMPTY STATE
// ============================================================================

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
      role="status"
      aria-label={title}
    >
      {icon && (
        <div className="mb-4 text-muted-foreground" aria-hidden="true">
          {React.isValidElement(icon) && React.cloneElement(icon, {
            className: 'h-16 w-16',
          } as Partial<unknown>)}
        </div>
      )}
      <h3 className="text-lg font-semibold text-foreground mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mb-4 max-w-sm leading-relaxed">
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </motion.div>
  );
};

// ============================================================================
// ERROR STATE
// ============================================================================

interface ErrorStateProps {
  title?: string;
  description?: string;
  error?: string;
  onRetry?: () => void;
  className?: string;
}

const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Ошибка',
  description,
  error,
  onRetry,
  className,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
      role="alert"
      aria-live="assertive"
    >
      <XCircle className="h-16 w-16 text-destructive mb-4" aria-hidden="true" />
      <h3 className="text-lg font-semibold text-foreground mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mb-2 leading-relaxed">{description}</p>
      )}
      {error && (
        <p className="text-xs text-destructive bg-destructive/10 px-3 py-2 rounded-lg mb-4 max-w-md">
          {error}
        </p>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          Попробовать снова
        </button>
      )}
    </motion.div>
  );
};

// ============================================================================
// ALERT
// ============================================================================

interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  onClose?: () => void;
  role?: 'alert' | 'status' | 'region';
}

const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  description,
  icon,
  action,
  className,
  onClose,
  role = 'status',
}) => {
  const variants = {
    info: {
      bg: 'bg-blue-50 dark:bg-blue-950/20',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-900 dark:text-blue-100',
      icon: <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />,
    },
    success: {
      bg: 'bg-green-50 dark:bg-green-950/20',
      border: 'border-green-200 dark:border-green-800',
      text: 'text-green-900 dark:text-green-100',
      icon: <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />,
    },
    warning: {
      bg: 'bg-yellow-50 dark:bg-yellow-950/20',
      border: 'border-yellow-200 dark:border-yellow-800',
      text: 'text-yellow-900 dark:text-yellow-100',
      icon: <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />,
    },
    error: {
      bg: 'bg-red-50 dark:bg-red-950/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-900 dark:text-red-100',
      icon: <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />,
    },
  };

  const variantStyles = variants[variant];

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border',
        variantStyles.bg,
        variantStyles.border,
        variantStyles.text,
        className
      )}
      role={role}
      aria-live={variant === 'error' ? 'assertive' : 'polite'}
    >
      {icon || variantStyles.icon}
      <div className="flex-1 min-w-0">
        {title && <p className="font-medium mb-0.5">{title}</p>}
        {description && <p className="text-sm opacity-90 leading-relaxed">{description}</p>}
        {action && <div className="mt-2">{action}</div>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Close alert"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
};

export { EmptyState, ErrorState, Alert };
