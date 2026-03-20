# Arizona Lavka Marketplace - Monitoring Stack

## 📊 Обзор

Стек мониторинга для Arizona Lavka Marketplace включает:

- **Prometheus** - сбор и хранение метрик
- **Grafana** - визуализация и дашборды
- **Node Exporter** - метрики хоста (CPU, память, диск, сеть)
- **Postgres Exporter** - метрики PostgreSQL

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Убедитесь что prometheus-client установлен
pip install -r backend/requirements.txt
```

### 2. Запуск мониторинга

```bash
# Запуск всего стека мониторинга
docker compose -f docker-compose.monitoring.yml up -d

# Проверка статуса
docker compose -f docker-compose.monitoring.yml ps

# Просмотр логов
docker compose -f docker-compose.monitoring.yml logs -f prometheus
```

### 3. Доступ к сервисам

| Сервис | URL | Credentials |
|--------|-----|-------------|
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Backend Metrics** | http://localhost:8000/metrics | - |

## 📈 Доступные метрики

### HTTP Metrics

| Метрика | Описание |
|---------|----------|
| `http_requests_total` | Всего HTTP запросов (method, endpoint, status) |
| `http_request_duration_seconds` | Длительность запросов (гистограмма) |
| `http_requests_in_progress` | Активные запросы |
| `http_responses_total` | Ответы по статус кодам |

### Authentication Metrics

| Метрика | Описание |
|---------|----------|
| `auth_logins_total` | Попытки входа (status, method) |
| `auth_registrations_total` | Попытки регистрации (status) |
| `auth_token_refreshes_total` | Обновления токенов (status) |
| `auth_email_verifications_total` | Верификации email (status) |

### Marketplace Metrics

| Метрика | Описание |
|---------|----------|
| `marketplace_offers_fetched_total` | Запросы данных marketplace (status) |
| `marketplace_offers_count` | Количество предложений (type) |
| `marketplace_cache_age_seconds` | Возраст кэша |
| `marketplace_circuit_breaker_state` | Состояние circuit breaker |

### Config Generator Metrics

| Метрика | Описание |
|---------|----------|
| `config_generations_total` | Генерации конфигов (status, mode) |
| `config_items_generated_total` | Сгенерированные предметы (mode) |
| `config_generation_duration_seconds` | Длительность генерации (mode) |
| `config_history_saves_total` | Сохранения в историю |

### Security Metrics

| Метрика | Описание |
|---------|----------|
| `security_blocked_ips` | Заблокированные IP |
| `security_suspicious_activities_total` | Подозрительная активность (type) |
| `security_turnstile_verifications_total` | Turnstile верификации (status) |

### External API Metrics

| Метрика | Описание |
|---------|----------|
| `external_api_requests_total` | Запросы к внешним API (api, status) |
| `external_api_request_duration_seconds` | Длительность запросов (api) |
| `external_api_circuit_breaker` | Circuit breaker состояние |

## 🔧 Конфигурация

### Prometheus

Конфигурация: `monitoring/prometheus.yml`

Основные настройки:
- Интервал сбора: 15s (global), 10s (backend)
- Хранение данных: 15 дней
- Targets: backend:8000, prometheus:9090

### Grafana

Провижининг:
- Datasources: `monitoring/grafana/provisioning/datasources/datasources.yml`
- Dashboards: `monitoring/grafana/provisioning/dashboards/dashboards.yml`

Дашборды:
- `backend-overview.json` - основной дашборд backend

## 📱 Дашборды

### Backend Overview

Основной дашборд включает:

1. **Верхние метрики (Stat panels)**
   - Requests per Second
   - Success Rate
   - p95 Latency
   - Active Requests

2. **HTTP Traffic**
   - Requests by Status Category (2xx, 4xx, 5xx)
   - Request Latency Percentiles (p50, p90, p95, p99)

3. **Business Metrics**
   - Authentication Attempts
   - Config Generations
   - Marketplace Offers Count
   - Circuit Breaker State

4. **Performance**
   - Config Generation Duration
   - External API Request Duration

5. **Security**
   - Suspicious Activities
   - Turnstile Verifications

## 🚨 Alerting (опционально)

Примеры alert правил можно добавить в `monitoring/alerts/`:

```yaml
groups:
  - name: arizonalavka-alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "p95 latency is {{ $value }}s"
```

## 🔍 Prometheus Queries

Полезные PromQL запросы:

```promql
# Requests per second
sum(rate(http_requests_total[5m]))

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# p95 latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Login success rate
sum(rate(auth_logins_total{status="success"}[5m])) / sum(rate(auth_logins_total[5m]))

# Config generation rate
sum(rate(config_generations_total{status="success"}[5m]))

# Marketplace cache age
marketplace_cache_age_seconds

# Circuit breaker state
marketplace_circuit_breaker_state
```

## 🛠️ Troubleshooting

### Prometheus не собирает метрики

```bash
# Проверка доступности metrics endpoint
curl http://localhost:8000/metrics

# Проверка targets в Prometheus
# Откройте http://localhost:9090/targets

# Логи Prometheus
docker compose -f docker-compose.monitoring.yml logs prometheus
```

### Grafana не показывает данные

1. Проверьте datasource (Configuration → Data Sources → Prometheus)
2. Убедитесь что Prometheus доступен из Grafana
3. Проверьте query в панели

### Метрики не обновляются

```bash
# Перезапуск backend
docker compose restart backend

# Проверка что middleware зарегистрирован
docker compose logs backend | grep "Prometheus middleware"
```

## 📊 Экспорт данных

### Экспорт метрик в формате Prometheus

```bash
curl http://localhost:8000/metrics
```

### Экспорт данных из Grafana

1. Откройте дашборд
2. Click Share → Export
3. Выберите формат (JSON, CSV, PNG)

## 🔐 Безопасность

### Ограничение доступа

Все сервисы доступны только на localhost:
- Prometheus: 127.0.0.1:9090
- Grafana: 127.0.0.1:3000
- Backend Metrics: 127.0.0.1:8000/metrics

Для доступа извне используйте reverse proxy (Nginx, Traefik) с аутентификацией.

### Смена паролей

```bash
# Смена пароля admin в Grafana
# UI: Configuration → Users → admin → Change Password

# Или через переменные окружения в docker-compose.monitoring.yml:
GF_SECURITY_ADMIN_USER=newadmin
GF_SECURITY_ADMIN_PASSWORD=newpassword
```

## 📚 Дополнительные ресурсы

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
