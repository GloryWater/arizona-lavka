import React, { forwardRef } from 'react';
import { cn } from '@/shared/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  children?: React.ReactNode;
  'aria-label'?: string;
  'aria-describedby'?: string;
  'data-testid'?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, icon, iconPosition = 'left', children, 'aria-label': ariaLabel, 'aria-describedby': ariaDescribedby, 'data-testid': dataTestId, ...props }, ref) => {
    const baseStyles = 'flex h-11 w-full rounded-lg border border-input bg-background px-4 py-2 ' +
      'text-sm ring-offset-background file:border-0 file:bg-transparent ' +
      'file:text-sm file:font-medium placeholder:text-muted-foreground ' +
      'transition-all duration-200 ease-in-out ' +
      'hover:border-ring/50 ' +
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ' +
      'focus-visible:ring-offset-2 focus-visible:border-ring ' +
      'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted/50';

    const iconStyles = icon || children ? (iconPosition === 'left' ? 'pl-10' : 'pr-10') : '';
    const errorStyles = error ? 'border-destructive focus-visible:ring-destructive' : '';
    const inputId = props.id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const errorId = `error-${inputId}`;
    const labelId = `label-${inputId}`;

    return (
      <div className="w-full">
        {label && (
          <label
            id={labelId}
            htmlFor={inputId}
            className="mb-1.5 block text-sm font-medium text-foreground transition-colors"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {icon && iconPosition === 'left' && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors pointer-events-none" aria-hidden="true">
              {icon}
            </div>
          )}
          <input
            id={inputId}
            type={type}
            className={cn(baseStyles, iconStyles, errorStyles, className)}
            ref={ref}
            aria-label={ariaLabel || (label ? undefined : undefined)}
            aria-describedby={error ? errorId : (ariaDescribedby || label ? labelId : undefined)}
            aria-invalid={!!error}
            data-testid={dataTestId}
            {...props}
          />
          {icon && iconPosition === 'right' && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors pointer-events-none" aria-hidden="true">
              {icon}
            </div>
          )}
          {children && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {children}
            </div>
          )}
        </div>
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-destructive flex items-center gap-1.5 animate-slide-up-fade" role="alert">
            <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

// ============================================================================
// TEXTAREA
// ============================================================================

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, 'aria-label': ariaLabel, 'aria-describedby': ariaDescribedby, ...props }, ref) => {
    const baseStyles = 'flex min-h-[80px] w-full rounded-lg border border-input bg-background px-4 py-2 ' +
      'text-sm ring-offset-background placeholder:text-muted-foreground ' +
      'transition-all duration-200 ease-in-out resize-none ' +
      'hover:border-ring/50 ' +
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ' +
      'focus-visible:ring-offset-2 focus-visible:border-ring ' +
      'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted/50';

    const errorStyles = error ? 'border-destructive focus-visible:ring-destructive' : '';
    const textareaId = props.id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
    const errorId = `error-${textareaId}`;
    const labelId = `label-${textareaId}`;

    return (
      <div className="w-full">
        {label && (
          <label
            id={labelId}
            htmlFor={textareaId}
            className="mb-1.5 block text-sm font-medium text-foreground transition-colors"
          >
            {label}
          </label>
        )}
        <textarea
          id={textareaId}
          className={cn(baseStyles, errorStyles, className)}
          ref={ref}
          aria-label={ariaLabel || (label ? undefined : undefined)}
          aria-describedby={error ? errorId : (ariaDescribedby || label ? labelId : undefined)}
          aria-invalid={!!error}
          {...props}
        />
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-destructive flex items-center gap-1.5 animate-slide-up-fade" role="alert">
            <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

// ============================================================================
// SELECT
// ============================================================================

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  'aria-label'?: string;
  'aria-describedby'?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, icon, children, 'aria-label': ariaLabel, 'aria-describedby': ariaDescribedby, ...props }, ref) => {
    const baseStyles = 'flex h-11 w-full rounded-lg border border-input bg-background px-4 py-2 ' +
      'text-sm ring-offset-background placeholder:text-muted-foreground ' +
      'transition-all duration-200 ease-in-out appearance-none cursor-pointer ' +
      'hover:border-ring/50 ' +
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ' +
      'focus-visible:ring-offset-2 focus-visible:border-ring ' +
      'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted/50 ' +
      'pr-10';

    const iconStyles = icon ? 'pl-10' : '';
    const errorStyles = error ? 'border-destructive focus-visible:ring-destructive' : '';
    const selectId = props.id || `select-${Math.random().toString(36).substr(2, 9)}`;
    const errorId = `error-${selectId}`;
    const labelId = `label-${selectId}`;

    return (
      <div className="w-full">
        {label && (
          <label
            id={labelId}
            htmlFor={selectId}
            className="mb-1.5 block text-sm font-medium text-foreground transition-colors"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors pointer-events-none" aria-hidden="true">
              {icon}
            </div>
          )}
          <select
            id={selectId}
            className={cn(baseStyles, iconStyles, errorStyles, className)}
            ref={ref}
            aria-label={ariaLabel || (label ? undefined : undefined)}
            aria-describedby={error ? errorId : (ariaDescribedby || label ? labelId : undefined)}
            aria-invalid={!!error}
            {...props}
          >
            {children}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground transition-colors" aria-hidden="true">
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </div>
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-destructive flex items-center gap-1.5 animate-slide-up-fade" role="alert">
            <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

export { Input, Textarea, Select };
