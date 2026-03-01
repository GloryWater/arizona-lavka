import React from 'react';
import { cn } from '@/shared/lib/utils';

// ============================================================================
// SKELETON
// ============================================================================

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'animate-pulse rounded-md bg-muted',
        'bg-gradient-to-r from-muted via-muted-foreground/10 to-muted',
        'bg-[length:200%_100%]',
        'animate-shimmer',
        className
      )}
      {...props}
    />
  )
);

Skeleton.displayName = 'Skeleton';

// ============================================================================
// SKELETON CARD
// ============================================================================

interface SkeletonCardProps {}

const SkeletonCard: React.FC<SkeletonCardProps> = () => {
  return (
    <div className="rounded-xl border bg-card p-6 shadow-md overflow-hidden">
      <div className="flex items-start justify-between mb-4">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-8 w-1/3 mb-4" />
      <div className="space-y-2">
        <div className="flex justify-between">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
        </div>
        <div className="flex justify-between">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
        </div>
        <div className="flex justify-between">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
        </div>
      </div>
      <Skeleton className="h-10 w-full mt-6 rounded-lg" />
    </div>
  );
};

// ============================================================================
// SKELETON TABLE
// ============================================================================

interface SkeletonTableProps {
  rows?: number;
  columns?: number;
}

const SkeletonTable: React.FC<SkeletonTableProps> = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="w-full">
      <div className="flex gap-4 mb-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-8 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 mb-4">
          {Array.from({ length: columns }).map((_, j) => (
            <Skeleton key={j} className="h-10 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
};

// ============================================================================
// SKELETON TEXT
// ============================================================================

interface SkeletonTextProps {
  lines?: number;
}

const SkeletonText: React.FC<SkeletonTextProps> = ({ lines = 3 }) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            'h-4 w-full',
            i === lines - 1 && 'w-2/3'
          )}
        />
      ))}
    </div>
  );
};

// ============================================================================
// SKELETON AVATAR
// ============================================================================

interface SkeletonAvatarProps {
  size?: 'sm' | 'md' | 'lg';
}

const SkeletonAvatar: React.FC<SkeletonAvatarProps> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-16 w-16',
  };

  return <Skeleton className={cn('rounded-full', sizeClasses[size])} />;
};

// ============================================================================
// SKELETON IMAGE
// ============================================================================

interface SkeletonImageProps {
  className?: string;
}

const SkeletonImage: React.FC<SkeletonImageProps> = ({ className }) => {
  return (
    <Skeleton className={cn('w-full h-48 object-cover', className)} />
  );
};

// ============================================================================
// SKELETON CIRCLE
// ============================================================================

interface SkeletonCircleProps {
  size?: 'sm' | 'md' | 'lg';
}

const SkeletonCircle: React.FC<SkeletonCircleProps> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  return <Skeleton className={cn('rounded-full', sizeClasses[size])} />;
};

export { 
  Skeleton, 
  SkeletonCard, 
  SkeletonTable, 
  SkeletonText, 
  SkeletonAvatar,
  SkeletonImage,
  SkeletonCircle,
};
