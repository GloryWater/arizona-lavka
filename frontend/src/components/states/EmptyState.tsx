import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({
  title = 'Нет данных',
  description = 'Здесь пока ничего нет',
  icon,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {icon || (
        <Inbox className="h-12 w-12 text-gray-500 mb-4" />
      )}
      {title && (
        <h3 className="text-lg font-medium text-white mb-1">
          {title}
        </h3>
      )}
      {description && (
        <p className="text-gray-400 mb-4">
          {description}
        </p>
      )}
      {action && (
        <div className="mt-2">
          {action}
        </div>
      )}
    </div>
  );
}
