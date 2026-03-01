import React from 'react';
import { cn } from '@/shared/lib/utils';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | number;
  className?: string;
  'aria-label'?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ 
  size = 'md', 
  className,
  'aria-label': ariaLabel = 'loading'
}) => {
  const sizeValue = typeof size === 'number' ? size : {
    sm: 16,
    md: 24,
    lg: 32,
  }[size];

  return (
    <svg
      className={cn('animate-spin', className)}
      style={{ width: sizeValue, height: sizeValue }}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-label={ariaLabel}
      role="status"
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
  );
};

export { Spinner };
