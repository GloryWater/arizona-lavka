/**
 * useMetrics - хук для отслеживания действий пользователя.
 *
 * Предоставляет методы для трекинга:
 * - Поиска
 * - Фильтров
 * - Генерации конфигов
 * - Экспорта
 * - Кликов по предложениям
 * - Других событий
 */

import { useCallback, useRef } from 'react';
import { metricsClient } from '@/shared/api/metrics';

type EventCategory = 'navigation' | 'action' | 'conversion';

interface EventOptions {
  /** Категория события */
  category?: EventCategory;
  /** Задержать отправку (debounce) */
  debounceMs?: number;
  /** Отключить трекинг */
  disabled?: boolean;
}

/**
 * Хук для отслеживания действий пользователя.
 */
export function useMetrics() {
  // Храним таймеры debounce для каждого типа события
  const debounceTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  /**
   * Отслеживает произвольное событие.
   */
  const trackEvent = useCallback(
    (
      eventType: string,
      category: EventCategory = 'action',
      eventData?: Record<string, unknown>,
      options: EventOptions = {}
    ) => {
      const { debounceMs = 0, disabled = false } = options;

      if (disabled) {
        return;
      }

      // Debounce logic
      if (debounceMs > 0) {
        const timerKey = eventType;
        if (debounceTimers.current[timerKey]) {
          clearTimeout(debounceTimers.current[timerKey]);
        }

        debounceTimers.current[timerKey] = setTimeout(() => {
          metricsClient.trackEvent(eventType, category, eventData);
        }, debounceMs);
      } else {
        metricsClient.trackEvent(eventType, category, eventData);
      }
    },
    []
  );

  /**
   * Отслеживает поиск.
   */
  const trackSearch = useCallback(
    (query: string, resultsCount: number) => {
      trackEvent(
        'search_performed',
        'action',
        { query, results_count: resultsCount },
        { debounceMs: 300 }
      );
    },
    [trackEvent]
  );

  /**
   * Отслеживает применение фильтра.
   */
  const trackFilter = useCallback(
    (filterType: string, filterValue: string) => {
      trackEvent(
        'filter_applied',
        'action',
        { filter_type: filterType, filter_value: filterValue },
        { debounceMs: 300 }
      );
    },
    [trackEvent]
  );

  /**
   * Отслеживает генерацию конфига.
   */
  const trackConfigGenerated = useCallback(
    (serverId: number, itemsCount: number, mode: string) => {
      trackEvent(
        'config_generated',
        'conversion',
        { server_id: serverId, items_count: itemsCount, mode },
        {}
      );
    },
    [trackEvent]
  );

  /**
   * Отслеживает экспорт конфига.
   */
  const trackConfigExported = useCallback(
    (format: 'json' | 'txt', itemsCount: number) => {
      trackEvent(
        'config_exported',
        'conversion',
        { format, items_count: itemsCount },
        {}
      );

      // Также тречим конверсию
      metricsClient.trackConversion('config_exported');
    },
    []
  );

  /**
   * Отслеживает просмотр лавки.
   */
  const trackLavkaViewed = useCallback(
    (lavkaUid: string, serverId: number) => {
      trackEvent(
        'lavka_viewed',
        'navigation',
        { lavka_uid: lavkaUid, server_id: serverId },
        {}
      );
    },
    [trackEvent]
  );

  /**
   * Отслеживает клик по предложению.
   */
  const trackOfferClicked = useCallback(
    (offerId: string, itemName: string, price: number) => {
      trackEvent(
        'offer_clicked',
        'action',
        { offer_id: offerId, item_name: itemName, price },
        {}
      );
    },
    [trackEvent]
  );

  /**
   * Отслеживает успешный логин.
   */
  const trackLoginCompleted = useCallback(
    (method: 'email' | 'telegram') => {
      trackEvent(
        'login_completed',
        'conversion',
        { method },
        {}
      );
    },
    []
  );

  /**
   * Отслеживает просмотр страницы премиума.
   */
  const trackPremiumViewed = useCallback(
    (source?: string) => {
      trackEvent(
        'premium_viewed',
        'navigation',
        { source: source || 'direct' },
        {}
      );
    },
    []
  );

  /**
   * Отслеживает ошибку.
   */
  const trackError = useCallback(
    (errorType: string, errorMessage: string, context?: Record<string, unknown>) => {
      trackEvent(
        'error_occurred',
        'action',
        { error_type: errorType, error_message: errorMessage, ...context },
        {}
      );
    },
    [trackEvent]
  );

  return {
    trackEvent,
    trackSearch,
    trackFilter,
    trackConfigGenerated,
    trackConfigExported,
    trackLavkaViewed,
    trackOfferClicked,
    trackLoginCompleted,
    trackPremiumViewed,
    trackError,
  };
}

export default useMetrics;
