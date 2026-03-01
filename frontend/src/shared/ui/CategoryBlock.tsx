import React from 'react';
import { cn } from '@/shared/lib/utils';

export interface CategoryBlockProps {
  name: string;
  selected: boolean;
  onClick: () => void;
  className?: string;
}

export const CategoryBlock: React.FC<CategoryBlockProps> = ({
  name,
  selected,
  onClick,
  className,
}) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all duration-200 min-h-[100px]',
        'hover:shadow-md hover:scale-[1.02]',
        selected
          ? 'border-primary bg-primary/5 shadow-md'
          : 'border-border bg-card hover:border-primary/50',
        className
      )}
    >
      <span className="text-sm font-medium text-foreground text-center">
        {name}
      </span>
      {selected && (
        <div className="mt-2 h-2 w-2 rounded-full bg-primary" />
      )}
    </button>
  );
};
