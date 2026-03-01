import { cva, type VariantProps } from 'class-variance-authority';
import React from 'react';
import { cn } from '@/shared/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium transition-all duration-200 ease-in-out ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ' +
  'disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed ' +
  'active:scale-[0.98] hover:scale-[1.02] ' +
  'select-none',
  {
    variants: {
      variant: {
        primary:
          'bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80 hover:shadow-md',
        outline:
          'border-2 border-input bg-background hover:bg-accent hover:text-accent-foreground hover:shadow-md',
        ghost:
          'hover:bg-accent hover:text-accent-foreground',
        link:
          'text-primary underline-offset-4 hover:underline hover:text-primary/80',
        destructive:
          'bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-lg shadow-destructive/25 hover:shadow-xl hover:shadow-destructive/30',
        success:
          'bg-success text-success-foreground hover:bg-success/90 shadow-lg shadow-success/25 hover:shadow-xl hover:shadow-success/30',
        warning:
          'bg-warning text-warning-foreground hover:bg-warning/90 shadow-lg shadow-warning/25 hover:shadow-xl hover:shadow-warning/30',
      },
      size: {
        sm: 'h-9 px-3 text-sm gap-1.5',
        md: 'h-11 px-5 text-sm gap-2',
        lg: 'h-13 px-8 text-base gap-2.5',
        icon: 'h-10 w-10',
        'icon-sm': 'h-8 w-8',
        'icon-lg': 'h-12 w-12',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  isLoading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  'aria-label'?: string;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      isLoading,
      icon,
      iconPosition = 'left',
      children,
      disabled,
      'aria-label': ariaLabel,
      ...props
    },
    ref
  ) => {
    const hasIconOnly = !children && icon;
    const effectiveSize = hasIconOnly ? (size === 'md' ? 'icon' : size) : size;
    
    return (
      <button
        className={cn(buttonVariants({ variant, size: effectiveSize, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        aria-label={ariaLabel || (hasIconOnly ? 'button' : undefined)}
        aria-busy={isLoading}
        {...props}
      >
        {isLoading ? (
          <svg
            className="h-5 w-5 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : iconPosition === 'left' && icon ? (
          <span className="flex-shrink-0" aria-hidden="true">{icon}</span>
        ) : null}
        {children}
        {iconPosition === 'right' && icon ? (
          <span className="flex-shrink-0" aria-hidden="true">{icon}</span>
        ) : null}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
