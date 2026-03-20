/**
 * MetricsProvider - провайдер метрик для приложения.
 *
 * Инициализирует систему метрик при запуске приложения
 * и предоставляет контекст для дочерних компонентов.
 */

import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { metricsClient } from '@/shared/api/metrics';
import { useSession } from './useSession';

interface MetricsContextValue {
  sessionId: string | null;
  trackPageView: (path: string, title?: string) => void;
  trackEvent: (
    eventType: string,
    category: 'navigation' | 'action' | 'conversion',
    data?: Record<string, unknown>
  ) => void;
  trackConversion: (
    type: string,
    value?: number,
    currency?: string
  ) => void;
}

const MetricsContext = createContext<MetricsContextValue | null>(null);

interface MetricsProviderProps {
  children: ReactNode;
  /** Отключить трекинг (для разработки/тестирования) */
  disabled?: boolean;
}

/**
 * Провайдер метрик для приложения.
 */
export function MetricsProvider({ children, disabled = false }: MetricsProviderProps) {
  const { getSessionId } = useSession({ autoInit: !disabled });
  const [sessionId, setSessionId] = React.useState<string | null>(null);

  // Инициализация при монтировании
  useEffect(() => {
    if (!disabled) {
      metricsClient.initialize();
      setSessionId(getSessionId());
    }
  }, [disabled, getSessionId]);

  // Обновляем session_id когда он изменится
  useEffect(() => {
    const updateSessionId = () => {
      setSessionId(getSessionId());
    };

    // Проверяем каждые 100мс в начале
    const interval = setInterval(updateSessionId, 100);
    const timeout = setTimeout(() => {
      clearInterval(interval);
      updateSessionId();
    }, 1000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [getSessionId]);

  const contextValue: MetricsContextValue = React.useMemo(
    () => ({
      sessionId,
      trackPageView: (path: string, title?: string) => {
        if (!disabled) {
          metricsClient.trackPageView(path, title);
        }
      },
      trackEvent: (
        eventType: string,
        category: 'navigation' | 'action' | 'conversion',
        data?: Record<string, unknown>
      ) => {
        if (!disabled) {
          metricsClient.trackEvent(eventType, category, data);
        }
      },
      trackConversion: (type: string, value?: number, currency?: string) => {
        if (!disabled) {
          metricsClient.trackConversion(type, value, currency);
        }
      },
    }),
    [sessionId, disabled]
  );

  return (
    <MetricsContext.Provider value={contextValue}>
      {children}
    </MetricsContext.Provider>
  );
}

/**
 * Хук для использования контекста метрик.
 */
export function useMetricsContext(): MetricsContextValue {
  const context = useContext(MetricsContext);
  if (!context) {
    throw new Error('useMetricsContext must be used within a MetricsProvider');
  }
  return context;
}

export default MetricsProvider;
