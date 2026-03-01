/**
 * Arizona Lavka Marketplace - k6 Load Test Script.
 *
 * © 2026 Arizona Lavka Marketplace. All Rights Reserved.
 * License: Proprietary Commercial License
 *
 * Alternative to Locust (higher performance).
 *
 * Usage:
 *   k6 run load_tests/k6_test.js
 *   k6 run --vus 100 --duration 3m load_tests/k6_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Кастомная метрика для ошибок
const errorRate = new Rate('errors');

// Конфигурация
export const options = {
  // Базовая конфигурация (переопределяется через CLI)
  vus: 50,
  duration: '3m',
  
  // Продвинутые сценарии (раскомментировать для детального теста)
  /*
  stages: [
    { duration: '1m', target: 50 },   // Разогрев до 50 пользователей
    { duration: '2m', target: 100 },  // Увеличение до 100
    { duration: '3m', target: 100 },  // Пик 100 пользователей
    { duration: '2m', target: 50 },   // Снижение до 50
    { duration: '1m', target: 0 },    // Остановка
  ],
  */
  
  // Пороги (тест провалится если не выполнены)
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% запросов < 2 секунд
    errors: ['rate<0.05'],              // Ошибки < 5%
  },
};

// Тестовые данные
const SERVERS = [0, 1, 2, 5, 10];
const MODES = ['SELL', 'BUY'];

// Базовый URL (передаётся через --host или env)
const BASE_URL = __ENV.HOST || 'https://lavka.glorysyntax.live';

/**
 * Сценарий: Обычный пользователь
 */
export default function () {
  // 1. Просмотр главной (лёгкий запрос)
  const homepageRes = http.get(`${BASE_URL}/`, {
    tags: { name: 'Homepage' },
  });
  check(homepageRes, {
    'homepage status is 200': (r) => r.status === 200,
  });
  errorRate.add(homepageRes.status !== 200);
  sleep(1);

  // 2. Просмотр списка лавок (средний запрос)
  const serverId = SERVERS[Math.floor(Math.random() * SERVERS.length)];
  const lavkasRes = http.get(
    `${BASE_URL}/api/marketplace/lavkas?server_id=${serverId}`,
    { tags: { name: 'Lavkas List' } }
  );
  check(lavkasRes, {
    'lavkas status is 200': (r) => r.status === 200,
  });
  errorRate.add(lavkasRes.status !== 200);
  sleep(1);

  // 3. Просмотр офферов (средний запрос)
  const offersRes = http.get(
    `${BASE_URL}/api/marketplace/offers?server_id=${serverId}`,
    { tags: { name: 'Offers List' } }
  );
  check(offersRes, {
    'offers status is 200': (r) => r.status === 200,
  });
  errorRate.add(offersRes.status !== 200);
  sleep(1);

  // 4. Генерация конфига (тяжёлый запрос)
  const mode = MODES[Math.floor(Math.random() * MODES.length)];
  const payload = JSON.stringify({
    server_id: serverId,
    mode: mode,
    percentage: Math.floor(Math.random() * 21) - 10, // -10 до +10
    save_to_history: false,
    min_liquidity: 0.0,
  });
  
  const configRes = http.post(
    `${BASE_URL}/api/config/generate`,
    payload,
    {
      tags: { name: 'Config Generate' },
      headers: { 'Content-Type': 'application/json' },
    }
  );
  
  check(configRes, {
    'config status is 200 or 401': (r) => r.status === 200 || r.status === 401,
  });
  errorRate.add(configRes.status >= 500);
  sleep(2);
}

/**
 * Хук перед началом теста
 */
export function handleSummary(data) {
  return {
    'load_tests/results/k6_summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const { metrics } = data;
  const reqs = metrics.http_reqs ? metrics.http_reqs.values.count : 0;
  const duration = metrics.http_req_duration ? metrics.http_req_duration.values : {};
  const errors = metrics.errors ? metrics.errors.values.count : 0;
  
  return `
============================================
k6 Load Test Summary
============================================
Total Requests: ${reqs}
Errors: ${errors}
Response Times:
  - Average: ${duration.avg ? duration.avg.toFixed(2) : 'N/A'}ms
  - 95th percentile: ${duration['p(95)'] ? duration['p(95)'].toFixed(2) : 'N/A'}ms
  - Max: ${duration.max ? duration.max.toFixed(2) : 'N/A'}ms
============================================`;
}
