import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '../ui/Button';

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = 'Ошибка',
  description = 'Произошла ошибка при загрузке данных',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <AlertTriangle className="h-12 w-12 text-red-500 mb-4" />
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
      {onRetry && (
        <Button onClick={onRetry} variant="primary" className="mt-2">
          Повторить
        </Button>
      )}
    </div>
  );
}
