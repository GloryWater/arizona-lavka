/**
 * usePageView - хук для автоматического отслеживания просмотров страниц.
 *
 * Использование:
 * - Вызывать в компонентах страниц
 * - Автоматически отправляет pageview при монтировании
 */

import { useEffect, useRef } from 'react';
import { metricsClient } from '@/shared/api/metrics';

interface UsePageViewOptions {
  /** Путь страницы (по умолчанию из window.location.pathname) */
  path?: string;
  /** Заголовок страницы (по умолчанию document.title) */
  title?: string;
  /** Отключить автоматическую отправку */
  disabled?: boolean;
}

/**
 * Хук для отслеживания просмотров страниц.
 */
export function usePageView(options: UsePageViewOptions = {}) {
  const {
    path,
    title,
    disabled = false,
  } = options;

  const initialPath = useRef(path || window.location.pathname);
  const initialTitle = useRef(title || document.title);
  const startTime = useRef(Date.now());

  useEffect(() => {
    if (disabled) {
      return;
    }

    const pagePath = path || initialPath.current;
    const pageTitle = title || initialTitle.current;

    // Отправляем pageview при монтировании
    metricsClient.trackPageView(
      pagePath,
      pageTitle,
      document.referrer || undefined,
      undefined // time_on_page будет рассчитан при unmount
    );

    // Отправляем время на странице при размонтировании
    return () => {
      const timeOnPage = Math.round((Date.now() - startTime.current) / 1000);
      metricsClient.trackPageView(
        pagePath,
        pageTitle,
        undefined,
        timeOnPage
      );
    };
  }, [disabled, path, title]);
}

export default usePageView;
