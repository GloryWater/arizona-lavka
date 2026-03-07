import { cva, type VariantProps } from 'class-variance-authority';
import React from 'react';
import { cn } from '@/shared/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all duration-200 ' +
  'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background ' +
  'select-none border',
  {
    variants: {
      variant: {
        primary:
          'bg-primary/10 text-primary hover:bg-primary/20 border-primary/20',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80 border-border',
        outline:
          'border-border text-foreground hover:bg-accent',
        success:
          'bg-success/10 text-success hover:bg-success/20 border-success/20',
        destructive:
          'bg-destructive/10 text-destructive hover:bg-destructive/20 border-destructive/20',
        warning:
          'bg-warning/10 text-warning hover:bg-warning/20 border-warning/20',
        neutral:
          'bg-muted text-muted-foreground hover:bg-muted/80 border-border',
        info:
          'bg-info/10 text-info hover:bg-info/20 border-info/20',
      },
      size: {
        sm: 'px-2 py-0.5 text-xs gap-1',
        md: 'px-3 py-1 text-xs gap-1.5',
        lg: 'px-4 py-1.5 text-sm gap-2',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode;
  'aria-label'?: string;
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant, size, icon, children, 'aria-label': ariaLabel, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(badgeVariants({ variant, size }), className)}
        {...props}
        aria-label={ariaLabel}
      >
        {icon && <span className="flex-shrink-0" aria-hidden="true">{icon}</span>}
        {children}
      </div>
    );
  }
);

Badge.displayName = 'Badge';

export { Badge, badgeVariants };
