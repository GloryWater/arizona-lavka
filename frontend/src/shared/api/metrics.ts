/**
 * Metrics API client - низкоуровневый клиент для отправки метрик.
 *
 * Особенности:
 * - Batch отправка событий (каждые 10с или 10 событий)
 * - Использование navigator.sendBeacon для надёжности при выгрузке страницы
 * - Очереди событий для офлайн-режима
 * - Never throw errors - метрики не должны влиять на UX
 */

// ============================================================================
// TYPES
// ============================================================================

export interface DeviceInfo {
  userAgent: string;
  screenResolution: string;
  language: string;
  platform: string;
  timezone: string;
}

export interface SessionStartPayload {
  session_id: string;
  utm_source?: string | null;
  utm_medium?: string | null;
  utm_campaign?: string | null;
  device_info: DeviceInfo;
}

export interface SessionEndPayload {
  session_id: string;
  duration?: number;
}

export interface PageViewPayload {
  session_id: string;
  page_path: string;
  page_title?: string | null;
  referrer?: string | null;
  time_on_page?: number | null;
}

export interface UserEventPayload {
  session_id: string;
  event_type: string;
  event_category: 'navigation' | 'action' | 'conversion';
  event_data?: Record<string, unknown> | null;
  error_message?: string | null;
}

export interface ConversionPayload {
  session_id: string;
  conversion_type: string;
  conversion_value?: number | null;
  currency?: string;
  attribution_source?: string | null;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const BATCH_SIZE = 10;
const BATCH_INTERVAL_MS = 10000; // 10 секунд
const MAX_QUEUE_SIZE = 1000;
const API_BASE = import.meta.env.VITE_API_URL || '/api';

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Генерирует UUID v4 для session_id.
 */
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }

  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Собирает информацию об устройстве.
 */
function getDeviceInfo(): DeviceInfo {
  return {
    userAgent: navigator.userAgent,
    screenResolution: `${screen.width}x${screen.height}`,
    language: navigator.language,
    platform: navigator.platform,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  };
}

/**
 * Получает UTM метки из URL.
 */
function getUTMParams(): { utm_source?: string; utm_medium?: string; utm_campaign?: string } {
  const params = new URLSearchParams(window.location.search);
  return {
    utm_source: params.get('utm_source') ?? undefined,
    utm_medium: params.get('utm_medium') ?? undefined,
    utm_campaign: params.get('utm_campaign') ?? undefined,
  };
}

// ============================================================================
// METRICS CLIENT CLASS
// ============================================================================

class MetricsClient {
  private sessionId: string | null = null;
  private eventQueue: Array<{ type: string; payload: unknown }> = [];
  private batchTimer: ReturnType<typeof setTimeout> | null = null;
  private isOnline = true;
  private initialized = false;

  constructor() {
    this.checkOnlineStatus();
    this.setupEventListeners();
  }

  // ==========================================================================
  // INITIALIZATION
  // ==========================================================================

  /**
   * Инициализирует метрики.
   * Должен быть вызван один раз при запуске приложения.
   */
  initialize(): void {
    if (this.initialized) {
      return;
    }

    this.initialized = true;

    // Пытаемся получить существующий session_id из localStorage
    const storedSessionId = localStorage.getItem('metrics_session_id');
    const storedSessionExpiry = localStorage.getItem('metrics_session_expiry');

    const now = Date.now();
    const expiry = storedSessionExpiry ? parseInt(storedSessionExpiry, 10) : 0;

    if (storedSessionId && now < expiry) {
      this.sessionId = storedSessionId;
      this.sendBatch(); // Отправляем накопленные события
    } else {
      // Создаём новую сессию
      this.startSession();
    }

    // Запускаем периодическую отправку
    this.startBatchTimer();
  }

  // ==========================================================================
  // SESSION MANAGEMENT
  // ==========================================================================

  /**
   * Начинает новую сессию.
   */
  async startSession(): Promise<string> {
    const sessionId = generateUUID();
    this.sessionId = sessionId;

    // Сохраняем в localStorage на 8 часов
    const expiry = Date.now() + 8 * 60 * 60 * 1000;
    localStorage.setItem('metrics_session_id', sessionId);
    localStorage.setItem('metrics_session_expiry', expiry.toString());

    const payload: SessionStartPayload = {
      session_id: sessionId,
      device_info: getDeviceInfo(),
      ...getUTMParams(),
    };

    await this.sendRequest('/metrics/session/start', payload);

    return sessionId;
  }

  /**
   * Завершает текущую сессию.
   */
  async endSession(): Promise<void> {
    if (!this.sessionId) {
      return;
    }

    const payload: SessionEndPayload = {
      session_id: this.sessionId,
    };

    // Используем sendBeacon для надёжности
    this.sendBeacon('/metrics/session/end', payload);

    // Очищаем
    this.sessionId = null;
    localStorage.removeItem('metrics_session_id');
    localStorage.removeItem('metrics_session_expiry');

    // Отправляем оставшиеся события
    await this.sendBatch();
  }

  // ==========================================================================
  // EVENT TRACKING
  // ==========================================================================

  /**
   * Отслеживает просмотр страницы.
   */
  async trackPageView(
    pagePath: string,
    pageTitle?: string,
    referrer?: string,
    timeOnPage?: number
  ): Promise<void> {
    if (!this.sessionId) {
      return;
    }

    const payload: PageViewPayload = {
      session_id: this.sessionId,
      page_path: pagePath,
      page_title: pageTitle || null,
      referrer: referrer || null,
      time_on_page: timeOnPage || null,
    };

    await this.sendRequest('/metrics/pageview', payload);
  }

  /**
   * Отслеживает действие пользователя.
   */
  async trackEvent(
    eventType: string,
    eventCategory: 'navigation' | 'action' | 'conversion',
    eventData?: Record<string, unknown>,
    errorMessage?: string
  ): Promise<void> {
    if (!this.sessionId) {
      return;
    }

    const payload: UserEventPayload = {
      session_id: this.sessionId,
      event_type: eventType,
      event_category: eventCategory,
      event_data: eventData || null,
      error_message: errorMessage || null,
    };

    // Добавляем в очередь для batch отправки
    this.queueEvent('event', payload);
  }

  /**
   * Отслеживает конверсию.
   */
  async trackConversion(
    conversionType: string,
    conversionValue?: number,
    currency?: string,
    attributionSource?: string
  ): Promise<void> {
    if (!this.sessionId) {
      return;
    }

    const payload: ConversionPayload = {
      session_id: this.sessionId,
      conversion_type: conversionType,
      conversion_value: conversionValue || null,
      currency: currency || 'RUB',
      attribution_source: attributionSource || null,
    };

    await this.sendRequest('/metrics/conversion', payload);
  }

  // ==========================================================================
  // BATCH PROCESSING
  // ==========================================================================

  /**
   * Добавляет событие в очередь.
   */
  private queueEvent(type: string, payload: unknown): void {
    if (this.eventQueue.length >= MAX_QUEUE_SIZE) {
      // Удаляем oldest событие при переполнении
      this.eventQueue.shift();
    }

    this.eventQueue.push({ type, payload });

    // Отправляем если набралось достаточно событий
    if (this.eventQueue.length >= BATCH_SIZE) {
      this.sendBatch();
    }
  }

  /**
   * Отправляет пакет событий.
   */
  private async sendBatch(): Promise<void> {
    if (this.eventQueue.length === 0) {
      return;
    }

    const events = [...this.eventQueue];
    this.eventQueue = [];

    try {
      await this.sendRequest('/metrics/event/batch', { events });
    } catch (error) {
      // Возвращаем события в очередь при ошибке
      this.eventQueue = [...events, ...this.eventQueue];
      console.error('[Metrics] Failed to send batch:', error);
    }
  }

  /**
   * Запускает таймер периодической отправки.
   */
  private startBatchTimer(): void {
    if (this.batchTimer) {
      clearInterval(this.batchTimer);
    }

    this.batchTimer = setInterval(() => {
      this.sendBatch();
    }, BATCH_INTERVAL_MS);
  }

  // ==========================================================================
  // HTTP REQUESTS
  // ==========================================================================

  /**
   * Отправляет POST запрос на сервер метрик.
   * Never throws - errors are logged silently.
   */
  private async sendRequest(endpoint: string, payload: unknown): Promise<void> {
    if (!this.isOnline) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        keepalive: true,
      });

      if (!response.ok) {
        console.warn(`[Metrics] API returned ${response.status}`);
      }
    } catch (error) {
      // Silent fail - метрики не должны влиять на UX
      console.debug('[Metrics] Request failed:', error);
    }
  }

  /**
   * Отправляет данные через sendBeacon (для выгрузки страницы).
   */
  private sendBeacon(endpoint: string, payload: unknown): void {
    if (!this.isOnline) {
      return;
    }

    try {
      const data = JSON.stringify(payload);
      const blob = new Blob([data], { type: 'application/json' });
      navigator.sendBeacon(`${API_BASE}${endpoint}`, blob);
    } catch (error) {
      console.debug('[Metrics] Beacon failed:', error);
    }
  }

  // ==========================================================================
  // EVENT LISTENERS
  // ==========================================================================

  /**
   * Настраивает обработчики событий.
   */
  private setupEventListeners(): void {
    // Отправка при закрытии вкладки
    window.addEventListener('beforeunload', () => {
      this.endSession();
    });

    // Отправка при потере видимости
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.endSession();
      }
    });

    // Восстановление соединения
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.sendBatch();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  /**
   * Проверяет текущий статус соединения.
   */
  private checkOnlineStatus(): void {
    this.isOnline = navigator.onLine;
  }

  // ==========================================================================
  // PUBLIC GETTERS
  // ==========================================================================

  /**
   * Получает текущий session_id.
   */
  getSessionId(): string | null {
    return this.sessionId;
  }

  /**
   * Принудительно связывает сессию с user_id после логина.
   * (Сервер автоматически обновит сессию при следующем запросе)
   */
  invalidateSession(): void {
    this.sessionId = null;
    localStorage.removeItem('metrics_session_id');
    localStorage.removeItem('metrics_session_expiry');
  }
}

// ============================================================================
// EXPORT SINGLETON
// ============================================================================

export const metricsClient = new MetricsClient();
export default metricsClient;
