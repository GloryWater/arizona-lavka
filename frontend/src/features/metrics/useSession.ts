/**
 * useSession - хук для управления сессией метрик.
 *
 * Отвечает за:
 * - Инициализацию сессии при запуске приложения
 * - Завершение сессии при уходе с сайта
 * - Привязку сессии к пользователю после логина
 */

import { useEffect, useCallback } from 'react';
import { metricsClient } from '@/shared/api/metrics';

interface UseSessionOptions {
  /** Автоматически инициализировать сессию при монтировании */
  autoInit?: boolean;
}

/**
 * Хук для управления сессией метрик.
 */
export function useSession(options: UseSessionOptions = {}) {
  const { autoInit = true } = options;

  // Инициализация при монтировании
  useEffect(() => {
    if (autoInit) {
      metricsClient.initialize();
    }

    // Cleanup при размонтировании
    return () => {
      // Не завершаем сессию полностью, так как компонент может просто обновляться
    };
  }, [autoInit]);

  /**
   * Принудительно начинает новую сессию.
   */
  const startSession = useCallback(async (): Promise<string | null> => {
    try {
      const sessionId = await metricsClient.startSession();
      return sessionId;
    } catch (error) {
      console.error('[useSession] Failed to start session:', error);
      return null;
    }
  }, []);

  /**
   * Завершает текущую сессию.
   */
  const endSession = useCallback(async (): Promise<void> => {
    try {
      await metricsClient.endSession();
    } catch (error) {
      console.error('[useSession] Failed to end session:', error);
    }
  }, []);

  /**
   * Сбрасывает сессию (например, после логина для создания новой).
   */
  const resetSession = useCallback((): void => {
    metricsClient.invalidateSession();
  }, []);

  /**
   * Получает текущий session_id.
   */
  const getSessionId = useCallback((): string | null => {
    return metricsClient.getSessionId();
  }, []);

  return {
    startSession,
    endSession,
    resetSession,
    getSessionId,
  };
}

export default useSession;
